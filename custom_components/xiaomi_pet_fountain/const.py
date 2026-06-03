DOMAIN = "xiaomi_pet_fountain"

CONF_USER_ID = "user_id"
CONF_SSECURITY = "ssecurity"
CONF_SERVICE_TOKEN = "service_token"
CONF_REGION = "region"
CONF_DEVICE_ID = "device_id"
CONF_DEVICE_NAME = "device_name"
CONF_SESSION = "session"

DEFAULT_REGION = "de"
DEFAULT_POLL_INTERVAL = 30

REGIONS = ["cn", "de", "us", "ru", "tw", "sg", "in", "i2"]

# Supported model patterns
MODEL_PATTERNS = ["pet_waterer"]

# MiOT property map  siid, piid
PROP_ON = (2, 1)
PROP_FAULT = (2, 2)
PROP_MODE = (2, 4)
PROP_WATER_SHORTAGE = (2, 10)
PROP_FILTER_LIFE_LEFT = (3, 1)
PROP_FILTER_LEFT_TIME = (3, 2)
PROP_BATTERY = (5, 1)

# MiOT action
ACTION_RESET_FILTER = (4, 1)

# Fault codes
FAULT_NONE = 0
FAULT_WATER_SHORTAGE = 1
FAULT_PUMP_BLOCKED = 2
FAULT_FILTER_EXPIRED = 3
FAULT_LID_REMOVED = 4

FAULT_LABELS = {
    FAULT_NONE: "none",
    FAULT_WATER_SHORTAGE: "water_shortage",
    FAULT_PUMP_BLOCKED: "pump_blocked",
    FAULT_FILTER_EXPIRED: "filter_expired",
    FAULT_LID_REMOVED: "lid_removed",
}

# Flow modes
MODE_SENSOR = 0
MODE_INTERMITTENT = 1
MODE_CONTINUOUS = 2

MODE_LABELS = {
    MODE_SENSOR: "sensor",
    MODE_INTERMITTENT: "intermittent",
    MODE_CONTINUOUS: "continuous",
}

MODE_VALUES = {v: k for k, v in MODE_LABELS.items()}

# Config entry data keys
DATA_COORDINATOR = "coordinator"
