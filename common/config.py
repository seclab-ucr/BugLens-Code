import os


__MSM_DIR = "../../msm-android-10"
__CMD_DIR = "../analyzers/res/suture-res"
PROJ_CONFIG = { 
    "msm-sound":{
        "proj_dir": __MSM_DIR,
        "cmd_file": __CMD_DIR + '/' + "sound_cmd/sound",
    },
    "msm-other":{
        "proj_dir": __MSM_DIR,
        "cmd_dir":  __CMD_DIR + '/' + "others",
    },
    "msm-other-driver-hid":{
        "proj_dir": __MSM_DIR,
        "cmd_file":  __CMD_DIR + '/' + "others/driver-hid",
    },
    "msm-other-driver-block": {
        "proj_dir": __MSM_DIR,
        "cmd_file":  __CMD_DIR + '/' + "others/driver-block",
    },
    "msm-other-driver-i2c": {
        "proj_dir": __MSM_DIR,
        "cmd_file":  __CMD_DIR + '/' + "others/driver-i2c",
    },
    "msm-other-driver-md": {
        "proj_dir": __MSM_DIR,
        "cmd_file":  __CMD_DIR + '/' + "others/driver-md",
    },
    "msm-other-driver-rtc": {
        "proj_dir": __MSM_DIR,
        "cmd_file":  __CMD_DIR + '/' + "others/driver-rtc",
    },
    "msm-other-driver-scsi": {
        "proj_dir": __MSM_DIR,
        "cmd_file":  __CMD_DIR + '/' + "others/driver-scsi",
    },
    "msm-other-driver-staging": {
        "proj_dir": __MSM_DIR,
        "cmd_file":  __CMD_DIR + '/' + "others/driver-staging",
    },
    "msm-other-gpu": {
        "proj_dir": __MSM_DIR,
        "cmd_file":  __CMD_DIR + '/' + "others/gpu",
    },
    "msm-other-input": {
        "proj_dir": __MSM_DIR,
        "cmd_file":  __CMD_DIR + '/' + "others/input",
    },
    "msm-other-net": {
        "proj_dir": __MSM_DIR,
        "cmd_file":  __CMD_DIR + '/' + "others/net",
    },
    "msm-other-spi": {
        "proj_dir": __MSM_DIR,
        "cmd_file":  __CMD_DIR + '/' + "others/spi",
    },
    "msm-other-tty": {
        "proj_dir": __MSM_DIR,
        "cmd_file":  __CMD_DIR + '/' + "others/tty",
    },
    "codeql/ioctl-to-cfu": {
        "proj_dir": "../msm-4.4-revision-2017-May-07--08-33-56/src/home/kev/work/QualComm/semmle_data/projects/msm-4.4/revision-2017-May-07--08-33-56/kernel",
        "sarif_file": "results.sarif",
    },
    "codeql/ioctl-to-overflow": {
        "proj_dir": "../msm-4.4-revision-2017-May-07--08-33-56/src/home/kev/work/QualComm/semmle_data/projects/msm-4.4/revision-2017-May-07--08-33-56/kernel",
        "sarif_file": "results-overflow.sarif",
    }
}

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", 5432)),
    "dbname": os.getenv("PGDATABASE", "lmsuture"),
    "user": os.getenv("PGUSER", "lmsuture_user"),
    "password": os.getenv("PGPASSWORD", "password1"),
}

MODEL_ABBR = {
    "sonnet": "claude-3-5-sonnet-latest",
    "opus": "claude-3-opus-latest",
    "haiku": "claude-3-5-haiku-latest",
    "ds": "deepseek-reasoner",
    "dsv3": "deepseek-chat"
}