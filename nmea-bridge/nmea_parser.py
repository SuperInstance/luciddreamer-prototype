"""
nmea_parser.py — Parses standard NMEA 0183 sentences.

Supports:
    $GPGGA  — GPS position (lat/lon/fix/satellites)
    $GPRMC  — Recommended minimum (position, course, speed, date)
    $SDDBT  — Depth below transducer (feet/meters/fathoms)
    $SDDPT  — Depth below transducer + offset
    $HDM    — Heading magnetic
    $HDT    — Heading true
    $HDG    — Heading (magnetic + deviation + variation)
    $MTW    — Water temperature
    $VHW    — Water speed and heading
    $XDR    — Transducer readings (engine RPM, tank levels, etc.)

Returns structured ParseResult objects.

Usage:
    parser = NMEAParser()
    result = parser.parse("$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47")
    if result:
        print(result.data)
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


# ─── Sentence Types ─────────────────────────────────────────────────────────

class SentenceType(Enum):
    GPGGA = "GPGGA"
    GPRMC = "GPRMC"
    SDDBT = "SDDBT"
    SDDPT = "SDDPT"
    HDM = "HDM"
    HDT = "HDT"
    HDG = "HDG"
    MTW = "MTW"
    VHW = "VHW"
    XDR = "XDR"
    UNKNOWN = "UNKNOWN"


# ─── Parse Result ───────────────────────────────────────────────────────────

@dataclass
class ParseResult:
    """Result of parsing a single NMEA sentence."""
    raw: str                           # Original sentence
    sentence_type: SentenceType        # Type identifier
    data: Dict[str, Any]               # Parsed fields
    checksum_valid: bool = True        # Was checksum correct?
    timestamp: float = field(default_factory=time.time)

    @property
    def valid(self) -> bool:
        return self.sentence_type != SentenceType.UNKNOWN and self.checksum_valid


# ─── Parser ─────────────────────────────────────────────────────────────────

class NMEAParser:
    """Parses NMEA 0183 sentences into structured data.

    Each parse() call returns a ParseResult or None for malformed input.
    The parser is stateless — it does not accumulate across calls.
    """

    # Regex to split a sentence into talker+type, body, checksum
    _SENTENCE_RE = re.compile(
        r'^\$([A-Z]{2})([A-Z]{3,5}),(.*)\*([0-9A-Fa-f]{2})$'
    )

    def parse(self, sentence: str) -> Optional[ParseResult]:
        """Parse a single NMEA sentence.

        Args:
            sentence: Raw NMEA sentence like "$GPGGA,...,*XX"

        Returns:
            ParseResult if recognized, None if malformed.
        """
        sentence = sentence.strip()
        if not sentence:
            return None

        # Some sentences may lack checksum
        if '*' not in sentence:
            # Try to parse without checksum
            if sentence.startswith('$'):
                parts = sentence[1:].split(',', 1)
                if len(parts) < 2:
                    return None
                talker_type = parts[0]
                body = parts[1]
                checksum_valid = True  # Can't verify
            else:
                return None
        else:
            match = self._SENTENCE_RE.match(sentence)
            if not match:
                return None

            talker, msg_type, body, checksum_hex = match.groups()
            talker_type = talker + msg_type

            # Verify checksum
            expected = int(checksum_hex, 16)
            computed = self._compute_checksum(sentence)
            checksum_valid = (expected == computed)

        # Determine sentence type and parse body
        # Strip the talker prefix ($GP, $SD, $HC, $II, etc.) to get the type
        msg_type = talker_type[2:] if len(talker_type) >= 5 else talker_type[2:]

        try:
            stype = SentenceType(msg_type)
        except ValueError:
            # Check for known types with different talker prefixes
            if msg_type == "GGA":
                stype = SentenceType.GPGGA
            elif msg_type == "RMC":
                stype = SentenceType.GPRMC
            elif msg_type == "DBT":
                stype = SentenceType.SDDBT
            elif msg_type == "DPT":
                stype = SentenceType.SDDPT
            elif msg_type == "HDM":
                stype = SentenceType.HDM
            elif msg_type == "HDT":
                stype = SentenceType.HDT
            elif msg_type == "HDG":
                stype = SentenceType.HDG
            elif msg_type == "MTW":
                stype = SentenceType.MTW
            elif msg_type == "VHW":
                stype = SentenceType.VHW
            elif msg_type == "XDR":
                stype = SentenceType.XDR
            else:
                return ParseResult(
                    raw=sentence,
                    sentence_type=SentenceType.UNKNOWN,
                    data={},
                    checksum_valid=checksum_valid,
                )

        # Dispatch to specific parser
        fields = body.split(',')
        parser_method = getattr(self, f'_parse_{stype.value.lower()}', None)
        if parser_method is None:
            return ParseResult(
                raw=sentence,
                sentence_type=stype,
                data={"raw_fields": fields},
                checksum_valid=checksum_valid,
            )

        data = parser_method(fields)
        return ParseResult(
            raw=sentence,
            sentence_type=stype,
            data=data,
            checksum_valid=checksum_valid,
        )

    @staticmethod
    def _compute_checksum(sentence: str) -> int:
        """Compute NMEA checksum (XOR of bytes between $ and *)."""
        start = sentence.find('$')
        end = sentence.rfind('*')
        if start == -1 or end == -1:
            return 0
        cs = 0
        for ch in sentence[start + 1:end]:
            cs ^= ord(ch)
        return cs

    # ─── Sentence-Specific Parsers ──

    @staticmethod
    def _parse_nmea_lat(fields: List[str], lat_idx: int, ns_idx: int) -> Optional[float]:
        """Parse NMEA latitude: DDMM.MMM,N/S → decimal degrees."""
        try:
            raw = fields[lat_idx]
            ns = fields[ns_idx]
            if not raw:
                return None
            deg = int(raw[:2])
            minutes = float(raw[2:])
            val = deg + minutes / 60.0
            if ns == 'S':
                val = -val
            return val
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _parse_nmea_lon(fields: List[str], lon_idx: int, ew_idx: int) -> Optional[float]:
        """Parse NMEA longitude: DDDMM.MMM,E/W → decimal degrees."""
        try:
            raw = fields[lon_idx]
            ew = fields[ew_idx]
            if not raw:
                return None
            deg = int(raw[:3])
            minutes = float(raw[3:])
            val = deg + minutes / 60.0
            if ew == 'W':
                val = -val
            return val
        except (ValueError, IndexError):
            return None

    def _parse_gpgga(self, fields: List[str]) -> Dict[str, Any]:
        """$GPGGA,time,lat,N/S,lon,E/W,fix_quality,num_sats,hdop,alt,M,geoid,M,dgps_age,dgps_id

        fix_quality: 0=invalid, 1=GPS fix, 2=DGPS, 3=PPS, 4=RTK, 5=Float RTK,
                     6=estimated, 7=manual, 8=simulation
        """
        return {
            "time": fields[0] if len(fields) > 0 else "",
            "latitude": self._parse_nmea_lat(fields, 1, 2),
            "longitude": self._parse_nmea_lon(fields, 3, 4),
            "fix_quality": self._safe_int(fields, 5, 0),
            "num_satellites": self._safe_int(fields, 6, 0),
            "hdop": self._safe_float(fields, 7),
            "altitude": self._safe_float(fields, 8),
            "altitude_units": fields[9] if len(fields) > 9 else "",
            "geoid_height": self._safe_float(fields, 10),
            "geoid_units": fields[11] if len(fields) > 11 else "",
        }

    def _parse_gprmc(self, fields: List[str]) -> Dict[str, Any]:
        """$GPRMC,time,status,lat,N/S,lon,E/W,speed_knots,course,date,mag_var,E/W

        status: A=active, V=void
        """
        speed = self._safe_float(fields, 6)
        course = self._safe_float(fields, 7)
        return {
            "time": fields[0] if len(fields) > 0 else "",
            "status": fields[1] if len(fields) > 1 else "V",
            "latitude": self._parse_nmea_lat(fields, 2, 3),
            "longitude": self._parse_nmea_lon(fields, 4, 5),
            "speed_knots": speed,
            "course_degrees": course,
            "date": fields[8] if len(fields) > 8 else "",
            "magnetic_variation": self._safe_float(fields, 9),
            "magnetic_var_dir": fields[10] if len(fields) > 10 else "",
        }

    def _parse_sddbt(self, fields: List[str]) -> Dict[str, Any]:
        """$SDDBT,depth_feet,f,depth_meters,M,depth_fathoms,F

        Depth below transducer in three units.
        """
        return {
            "depth_feet": self._safe_float(fields, 0),
            "depth_meters": self._safe_float(fields, 2),
            "depth_fathoms": self._safe_float(fields, 4),
        }

    def _parse_sddpt(self, fields: List[str]) -> Dict[str, Any]:
        """$SDDPT,depth_meters,offset_from_transducer,max_depth

        Depth below transducer with offset.
        """
        depth_m = self._safe_float(fields, 0)
        offset = self._safe_float(fields, 1)
        max_depth = self._safe_float(fields, 2)
        return {
            "depth_meters": depth_m,
            "transducer_offset": offset,
            "max_depth": max_depth,
            "depth_fathoms": depth_m / 1.8288 if depth_m is not None else None,
        }

    def _parse_hdm(self, fields: List[str]) -> Dict[str, Any]:
        """$HDM,heading,M"""
        return {
            "heading": self._safe_float(fields, 0),
            "type": "magnetic",
        }

    def _parse_hdt(self, fields: List[str]) -> Dict[str, Any]:
        """$HDT,heading,T"""
        return {
            "heading": self._safe_float(fields, 0),
            "type": "true",
        }

    def _parse_hdg(self, fields: List[str]) -> Dict[str, Any]:
        """$HDG,magnetic_heading,deviation,E/W,variation,E/W"""
        heading = self._safe_float(fields, 0)
        dev = self._safe_float(fields, 1)
        dev_dir = fields[2] if len(fields) > 2 else ""
        var = self._safe_float(fields, 3)
        var_dir = fields[4] if len(fields) > 4 else ""

        # Apply deviation and variation to get true heading
        true_heading = heading
        if dev is not None:
            true_heading += dev if dev_dir != 'W' else -dev
        if var is not None:
            true_heading += var if var_dir != 'W' else -var
        true_heading = true_heading % 360.0 if true_heading is not None else None

        return {
            "heading_magnetic": heading,
            "deviation": dev,
            "deviation_dir": dev_dir,
            "variation": var,
            "variation_dir": var_dir,
            "heading_true": true_heading,
        }

    def _parse_mtw(self, fields: List[str]) -> Dict[str, Any]:
        """$MTW,temperature,C"""
        return {
            "water_temperature": self._safe_float(fields, 0),
            "units": fields[1] if len(fields) > 1 else "C",
        }

    def _parse_vhw(self, fields: List[str]) -> Dict[str, Any]:
        """$VHW,heading_true,T,heading_magnetic,M,speed_knots,N,speed_kmh,K"""
        return {
            "heading_true": self._safe_float(fields, 0),
            "heading_magnetic": self._safe_float(fields, 2),
            "speed_knots": self._safe_float(fields, 4),
            "speed_kmh": self._safe_float(fields, 6),
        }

    def _parse_xdr(self, fields: List[str]) -> Dict[str, Any]:
        """$XDR,transducer_type,value,unit,name[,transducer_type,...]

        XDR is a catch-all for transducer readings. Common types for vessels:
        - RPM: engine RPM
        - TANK: fuel tank level
        - VOLT: battery voltage
        - BARO: barometric pressure
        - TEMP: temperature
        - HUMD: humidity

        Multiple transducer readings can be in one sentence.
        """
        readings = []
        i = 0
        while i + 2 < len(fields):
            t_type = fields[i].strip()
            value = self._safe_float(fields, i + 1)
            unit = fields[i + 2].strip() if i + 2 < len(fields) else ""
            name = fields[i + 3].strip() if i + 3 < len(fields) else ""

            if t_type:
                readings.append({
                    "type": t_type,
                    "value": value,
                    "unit": unit,
                    "name": name,
                })

            # XDR groups are 4 fields each: type, value, unit, name
            # But some implementations use 3 (no name) — handle both
            if name:
                i += 4
            else:
                i += 3

        return {
            "transducers": readings,
            # Convenience extracts for common vessel readings
            "engine_rpm": self._find_reading(readings, "RPM"),
            "tank_level": self._find_reading(readings, "TANK"),
            "battery_voltage": self._find_reading(readings, "VOLT"),
            "barometric_pressure": self._find_reading(readings, "BARO"),
        }

    # Mapping from XDR short type codes to canonical names
    _XDR_TYPE_MAP = {
        "R": "RPM",
        "T": "TANK",  # Can also be TEMPERATURE — disambiguate by unit/name
        "V": "VOLT",
        "P": "PRESSURE",
        "C": "TEMPERATURE",
        "H": "HUMIDITY",
        "B": "BARO",
        "A": "ANGLE",
        "D": "DISTANCE",
        "F": "FREQUENCY",
        "G": "GFORCE",
        "L": "LUMINANCE",
        "M": "MASS",
        "O": "PITCH",
        "S": "SALINITY",
        "U": "VOLTAGE_DC",
        "X": "BOOLEAN",
    }

    @classmethod
    def _find_reading(cls, readings: List[Dict], type_name: str) -> Optional[float]:
        """Extract a value from XDR readings by transducer type.

        Matches on both the canonical name (e.g. 'RPM') and the short
        type code (e.g. 'R'). For ambiguous types like 'T' (TANK vs TEMPERATURE),
        checks the unit/name for disambiguation.
        """
        # Build reverse lookup: canonical → short code
        name_to_code = {v: k for k, v in cls._XDR_TYPE_MAP.items()}
        short_code = name_to_code.get(type_name, type_name)

        for r in readings:
            rtype = r["type"].upper()
            # Direct match on short code
            if rtype == short_code:
                # Disambiguate T (TANK vs TEMPERATURE) by name
                if type_name == "TANK" and r.get("name", "").upper() in ("FUEL", "WATER", "OIL"):
                    return r["value"]
                if type_name == "TANK":
                    continue
                if type_name == "TEMPERATURE" and r.get("unit", "").upper() == "C":
                    return r["value"]
                if type_name != "TANK" and type_name != "TEMPERATURE":
                    return r["value"]
            # Direct match on canonical name
            if rtype == type_name:
                return r["value"]
        return None

    # ─── Helpers ──

    @staticmethod
    def _safe_float(fields: List[str], idx: int) -> Optional[float]:
        try:
            val = fields[idx]
            return float(val) if val else None
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _safe_int(fields: List[str], idx: int, default: int = 0) -> int:
        try:
            val = fields[idx]
            return int(val) if val else default
        except (ValueError, IndexError):
            return default


# ─── Convenience ────────────────────────────────────────────────────────────

def parse_sentence(sentence: str) -> Optional[ParseResult]:
    """One-shot parse of an NMEA sentence."""
    return NMEAParser().parse(sentence)
