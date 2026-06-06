DOMAIN = "draytek_dsl"
DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 60

# Ordered list of paths to try for the DSL diagnostics page.
# DrayTek uses .sht (server-side HTML template) files for status pages.
DSL_STATUS_PATHS = [
    "/doc/dslstatus.sht",
    "/doc/DSLStatus.sht",
    "/doc/dslstatusinfo.sht",
    "/doc/vdslstatus.sht",
    "/doc/adslstatus.sht",
]
