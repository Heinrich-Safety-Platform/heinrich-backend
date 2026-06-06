import math


class ExifService:
    def validate_location(self, exif_gps: dict, lat: float, lng: float) -> tuple[bool, float]:
        if not exif_gps:
            return False, -1.0
        try:
            def dms_to_dd(dms) -> float:
                d, m, s = float(dms[0]), float(dms[1]), float(dms[2])
                return d + m / 60.0 + s / 3600.0

            exif_lat = dms_to_dd(exif_gps["GPSLatitude"])
            exif_lng = dms_to_dd(exif_gps["GPSLongitude"])

            if exif_gps.get("GPSLatitudeRef") == "S":
                exif_lat = -exif_lat
            if exif_gps.get("GPSLongitudeRef") == "W":
                exif_lng = -exif_lng

            dist_m = self._haversine(exif_lat, exif_lng, lat, lng)
            return True, dist_m
        except Exception:
            return False, -1.0

    def calc_trust_score(self, dist_m: float) -> float:
        if dist_m == -1.0:
            return 0.7
        if dist_m <= 0.0:
            return 1.0
        if dist_m >= 100.0:
            return 0.0
        return round(1.0 - (dist_m / 100.0), 2)

    @staticmethod
    def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        R = 6371000.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lng2 - lng1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.asin(math.sqrt(a))
