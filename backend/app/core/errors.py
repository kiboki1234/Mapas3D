class City3DError(Exception):
    """Error controlado que puede mostrarse al usuario."""


class ProviderUnavailableError(City3DError):
    pass


class InvalidGeospatialDataError(City3DError):
    pass


class GenerationCancelledError(City3DError):
    pass

