from enum import Enum


class Punishment(str, Enum):
    BAN = "ban"
    KICK = "kick"
    MUTE = "timeout"
    TIMEOUT = "timeout"
    STRIP = "strip"
    STRIPSTAFF = "stripstaff"