__MSM_DIR = "../msm-android-10"
PROJ_CONFIG = { 
    "msm-sound":{
        "proj_dir": __MSM_DIR,
        "cmd_file": "all_sound.cmd",
    },
    "msm-other":{
        "proj_dir": __MSM_DIR,
        "cmd_dir": "../msm-android-all"
    },
    "msm-other-driver-hid":{
        "proj_dir": __MSM_DIR,
        "cmd_file": "../msm-android-all/driver-hid",
    },
    "msm-other-driver-block": {
        "proj_dir": __MSM_DIR,
        "cmd_file": "../msm-android-all/driver-block",
    },
    "msm-other-driver-i2c": {
        "proj_dir": __MSM_DIR,
        "cmd_file": "../msm-android-all/driver-i2c",
    },
    "msm-other-driver-md": {
        "proj_dir": __MSM_DIR,
        "cmd_file": "../msm-android-all/driver-md",
    },
    "msm-other-driver-rtc": {
        "proj_dir": __MSM_DIR,
        "cmd_file": "../msm-android-all/driver-rtc",
    },
    "msm-other-driver-scsi": {
        "proj_dir": __MSM_DIR,
        "cmd_file": "../msm-android-all/driver-scsi",
    },
    "msm-other-driver-staging": {
        "proj_dir": __MSM_DIR,
        "cmd_file": "../msm-android-all/driver-staging",
    },
    "msm-other-gpu": {
        "proj_dir": __MSM_DIR,
        "cmd_file": "../msm-android-all/gpu",
    },
    "msm-other-input": {
        "proj_dir": __MSM_DIR,
        "cmd_file": "../msm-android-all/input",
    },
    "msm-other-net": {
        "proj_dir": __MSM_DIR,
        "cmd_file": "../msm-android-all/net",
    },
    "msm-other-spi": {
        "proj_dir": __MSM_DIR,
        "cmd_file": "../msm-android-all/spi",
    },
    "msm-other-tty": {
        "proj_dir": __MSM_DIR,
        "cmd_file": "../msm-android-all/tty",
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
    "host": "localhost",
    "port": 5432,
    "dbname": "lmsuture",
    "user": "lmsuture_user",
    "password": "password1",
}

MODEL_ABBR = {
    "sonnet": "claude-3-5-sonnet-latest",
    "opus": "claude-3-opus-latest",
    "haiku": "claude-3-5-haiku-latest",
    "ds": "deepseek-reasoner",
    "dsv3": "deepseek-chat"
}