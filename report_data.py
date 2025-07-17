# -------------------------
# --- Report Data Class ---
# -------------------------
class ReportData:
    def __init__(self, file_name, version, point_format,
        num_points, bounds, x_axis_bounds, y_axis_bounds,
        file_source=None, global_encoding=None, system_id=None, gen_software=None,
        creation_date=None, unique_classes=None, class_counts=None, unique_returns=None,
        return_counts=None, min_intensity=None, max_intensity=None, min_time=None,
        max_time=None, area=None, density=None
    ):
        # -- Metadata --
        self.file_name = file_name
        self.file_source = file_source
        self.global_encoding = global_encoding
        self.system_id = system_id
        self.gen_software = gen_software
        self.version = version
        self.point_format = point_format
        self.creation_date = creation_date

        # -- Classifications and Returns --
        self.unique_classes = unique_classes
        self.class_counts = class_counts

        self.unique_returns = unique_returns
        self.return_counts = return_counts

        # -- Intensity --
        self.min_intensity = min_intensity
        self.max_intensity = max_intensity

        # -- GPS Time --
        self.min_time = min_time
        self.max_time = max_time

        # -- Spatial Measures --
        self.num_points = num_points
        self.area = area
        self.density = density
        self.bounds = bounds
        self.x_axis_bounds = x_axis_bounds
        self.y_axis_bounds = y_axis_bounds
