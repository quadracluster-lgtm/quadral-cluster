from enum import StrEnum


class Quadra(StrEnum):
    ALPHA = "alpha"
    BETA = "beta"
    GAMMA = "gamma"
    DELTA = "delta"


class SocType(StrEnum):
    ILE = "ILE"
    SEI = "SEI"
    ESE = "ESE"
    LII = "LII"
    SLE = "SLE"
    IEI = "IEI"
    EIE = "EIE"
    LSI = "LSI"
    SEE = "SEE"
    ESI = "ESI"
    LIE = "LIE"
    ILI = "ILI"
    IEE = "IEE"
    EII = "EII"
    LSE = "LSE"
    SLI = "SLI"


QUADRA_MEMBERS = {
    Quadra.ALPHA: {SocType.ILE, SocType.SEI, SocType.ESE, SocType.LII},
    Quadra.BETA: {SocType.SLE, SocType.IEI, SocType.EIE, SocType.LSI},
    Quadra.GAMMA: {SocType.SEE, SocType.ESI, SocType.LIE, SocType.ILI},
    Quadra.DELTA: {SocType.IEE, SocType.EII, SocType.LSE, SocType.SLI},
}
