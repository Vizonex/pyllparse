CONTAINER_KEY = "c"
LABEL_PREFIX = ""
STATE_PREFIX = "s_n_"
STATE_ERROR = "s_error"
BLOB_PREFIX = "llparse_blob"
ARG_STATE = "state"
ARG_POS = "p"
ARG_ENDPOS = "endp"
VAR_MATCH = "match"

# MatchSequence

SEQUENCE_COMPLETE = "kMatchComplete"
SEQUENCE_MISMATCH = "kMatchMismatch"
SEQUENCE_PAUSE = "kMatchPause"


# I Thought it might be a little but faster to use tuples instead of lists - Vizonex
SIGNED_LIMITS: dict[str, tuple[str, str]] = {
    "i8": ("-0x80", "0x7f"),
    "i16": ("-0x8000", "0x7fff"),
    "i32": ("(-0x7fffffff - 1)", "0x7fffffff"),
    "i64": ("(-0x7fffffffffffffffLL - 1)", "0x7fffffffffffffffLL"),
}

# TODO (Vizonex) : Propose changes to llparse
# typescript program which uses two i8's
# which I belive is an error and a mistake
UNSIGNED_LIMITS: dict[str, tuple[str, str]] = {
    "i8": ("0", "0xff"),
    "i16": ("0", "0xffff"),
    "i32": ("0", "0xffffffff"),
    "i64": ("0ULL", "0xffffffffffffffffULL"),
}

UNSIGNED_TYPES: dict[str, str] = {
    "i8": "int8_t",
    "i16": "int16_t",
    "i32": "int32_t",
    "i64": "int64_t",
}

SIGNED_TYPES: dict[str, str] = {
    "i8": "int8_t",
    "i16": "int16_t",
    "i32": "int32_t",
    "i64": "int64_t",
}
