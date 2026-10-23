"""
Boleto barcode and linha digitável rules.

Pure functions only - no PDF or image handling - so every rule here can be tested
directly. Two kinds of boleto share the 44-digit barcode:

- bank boletos (ficha de compensação): linha digitável of 47 digits
- arrecadação (utility and tax bills, barcode starts with 8): linha of 48 digits

Every number this package returns has passed its check digits. Barcode symbols
(Interleaved 2 of 5) carry no checksum of their own and PDFs are full of long
digit runs, so the check digits are the only thing separating a boleto from noise.
"""

import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Callable, Dict, List, Optional

_BARCODE_RE = re.compile(r'[0-9]{44}')

# Printed linhas digitáveis, with the separators issuers commonly use. Matched as
# lookaheads so overlapping candidates are all tried: a near-miss that fails its
# check digits must not swallow the digits of a real linha next to it.
# [0-9] rather than \d, which also matches non-ASCII digits.
_BANK_LINHA_RE = re.compile(
    r'(?<![0-9])(?=('
    r'[0-9]{5}[.\s]?[0-9]{5}\s*'
    r'[0-9]{5}[.\s]?[0-9]{6}\s*'
    r'[0-9]{5}[.\s]?[0-9]{6}\s*'
    r'[0-9]\s*'
    r'[0-9]{14}'
    r')(?![0-9]))'
)
_ARRECADACAO_LINHA_RE = re.compile(
    r'(?<![0-9])(?=('
    r'8[0-9]{10}[-\s]?[0-9]\s*'
    r'[0-9]{11}[-\s]?[0-9]\s*'
    r'[0-9]{11}[-\s]?[0-9]\s*'
    r'[0-9]{11}[-\s]?[0-9]'
    r')(?![0-9]))'
)
_NON_DIGITS_RE = re.compile(r'[^0-9]')

# The due date factor counts days from a base date. It reached 9999 on 2025-02-21
# and restarted at 1000 the next day, so each factor now names two dates.
_FACTOR_BASE = date(1997, 10, 7)
_FACTOR_RESTART = date(2025, 2, 22)

# Arrecadação segment, the barcode's second digit.
_SEGMENTS = {
    '1': 'Municipal',
    '2': 'Water and sanitation',
    '3': 'Electricity and gas',
    '4': 'Telecommunications',
    '5': 'Government',
    '6': 'Carnês and other companies',
    '7': 'Traffic fines',
    '9': 'Bank use',
}


def mod10(digits: str) -> int:
    """Modulo 10 check digit: weights 2,1,2,1... from the right, digits of products summed."""
    total = 0
    weight = 2
    for d in reversed(digits):
        product = int(d) * weight
        total += product // 10 + product % 10
        weight = 1 if weight == 2 else 2
    return (10 - total % 10) % 10


def _mod11_remainder(digits: str) -> int:
    total = 0
    weight = 2
    for d in reversed(digits):
        total += int(d) * weight
        weight = 2 if weight == 9 else weight + 1
    return total % 11


def mod11(digits: str) -> int:
    """Modulo 11 check digit as arrecadação uses it: remainders 0 and 1 give 0."""
    rest = _mod11_remainder(digits)
    return 0 if rest in (0, 1) else 11 - rest


def mod11_bank(digits: str) -> int:
    """Modulo 11 for a bank barcode's general check digit: 0, 10 and 11 become 1."""
    dv = 11 - _mod11_remainder(digits)
    return 1 if dv in (0, 10, 11) else dv


def _arrecadacao_check(value_id: str) -> Optional[Callable[[str], int]]:
    """The check digit algorithm an arrecadação value identifier selects, if any."""
    if value_id in '67':
        return mod10
    if value_id in '89':
        return mod11
    return None


def _is_44_digits(barcode) -> bool:
    return isinstance(barcode, str) and _BARCODE_RE.fullmatch(barcode) is not None


def is_valid_barcode(barcode: str) -> bool:
    """True if `barcode` is a 44-digit boleto barcode whose general check digit is correct."""
    if not _is_44_digits(barcode):
        return False
    if barcode[0] == '8':
        check = _arrecadacao_check(barcode[2])
        return check is not None and int(barcode[3]) == check(barcode[:3] + barcode[4:])
    return int(barcode[4]) == mod11_bank(barcode[:4] + barcode[5:])


def barcode_to_linha(barcode: str) -> Optional[str]:
    """
    Convert a 44-digit barcode to its linha digitável: 47 digits for bank boletos,
    48 for arrecadação. Returns None if the input is not 44 digits, or is an
    arrecadação barcode with an unknown value identifier.
    """
    if not _is_44_digits(barcode):
        return None

    if barcode[0] != '8':
        # Three fields, each followed by its own modulo 10 check digit, then the
        # barcode's general check digit and the due date factor plus amount:
        # 9+1 10+1 10+1 1 14 = 47.
        fields = [barcode[0:4] + barcode[19:24], barcode[24:34], barcode[34:44]]
        return ''.join(f + str(mod10(f)) for f in fields) + barcode[4] + barcode[5:19]

    # Four 11-digit blocks, each followed by its own check digit: 4 x (11+1) = 48.
    # The third digit (value identifier) picks the algorithm: 6/7 -> mod 10, 8/9 -> mod 11.
    check = _arrecadacao_check(barcode[2])
    if check is None:
        return None
    blocks = [barcode[i:i + 11] for i in range(0, 44, 11)]
    return ''.join(block + str(check(block)) for block in blocks)


def linha_to_barcode(linha: str) -> Optional[str]:
    """
    Convert a 47- or 48-digit linha digitável back to its barcode. Returns None
    unless every check digit in the linha and in the resulting barcode is correct.
    """
    if not isinstance(linha, str) or not linha.isascii() or not linha.isdigit():
        return None

    if len(linha) == 47:
        fields = [linha[0:10], linha[10:21], linha[21:32]]
        if any(mod10(f[:-1]) != int(f[-1]) for f in fields):
            return None
        barcode = linha[0:4] + linha[32] + linha[33:47] + linha[4:9] + linha[10:20] + linha[21:31]
    elif len(linha) == 48 and linha[0] == '8':
        check = _arrecadacao_check(linha[2])
        if check is None:
            return None
        blocks = [linha[i:i + 12] for i in range(0, 48, 12)]
        if any(check(b[:11]) != int(b[11]) for b in blocks):
            return None
        barcode = ''.join(b[:11] for b in blocks)
    else:
        return None

    return barcode if is_valid_barcode(barcode) else None


def format_linha(linha: str) -> str:
    """
    Group a linha digitável the way it is printed on the boleto. Anything that is
    not 47 or 48 digits long is returned unchanged.

    Bank (47):         AAAAA.AAAAA BBBBB.BBBBBB CCCCC.CCCCCC D EEEEEEEEEEEEEE
    Arrecadação (48):  XXXXXXXXXXX-X XXXXXXXXXXX-X XXXXXXXXXXX-X XXXXXXXXXXX-X
    """
    if not linha:
        return linha
    if len(linha) == 48:
        return " ".join(f"{linha[i:i + 11]}-{linha[i + 11]}" for i in range(0, 48, 12))
    if len(linha) == 47:
        return (
            f"{linha[0:5]}.{linha[5:10]} "
            f"{linha[10:15]}.{linha[15:21]} "
            f"{linha[21:26]}.{linha[26:32]} "
            f"{linha[32]} "
            f"{linha[33:47]}"
        )
    return linha


def find_barcodes_in_text(text: str) -> List[str]:
    """
    Find the boletos whose linha digitável is printed in `text`, returning their
    44-digit barcodes in order of appearance, without duplicates.

    Bare 44-digit runs are deliberately not accepted: invoices print 44-digit
    NF-e access keys, and a single modulo 11 digit would let one in about one
    time in eleven. A linha carries four or five check digits.
    """
    if not text:
        return []

    found: Dict[int, str] = {}
    for pattern in (_BANK_LINHA_RE, _ARRECADACAO_LINHA_RE):
        for match in pattern.finditer(text):
            barcode = linha_to_barcode(_NON_DIGITS_RE.sub('', match.group(1)))
            if barcode:
                found.setdefault(match.start(), barcode)

    unique: List[str] = []
    for _, barcode in sorted(found.items()):
        if barcode not in unique:
            unique.append(barcode)
    return unique


def format_brl(amount: Decimal) -> str:
    """Format an amount in reais the Brazilian way: R$ 1.234,56."""
    return 'R$ ' + f'{amount:,.2f}'.translate(str.maketrans(',.', '.,'))


@dataclass(frozen=True)
class BoletoInfo:
    """A validated boleto and what its barcode says about the payment."""

    barcode: str
    linha: str
    kind: str                   # 'bank' or 'arrecadacao'
    amount: Optional[Decimal]   # None when the barcode leaves it to the payer
    due_date: Optional[date]    # bank boletos only; arrecadação has no standard field
    segment: Optional[str]      # arrecadação only

    @property
    def formatted(self) -> str:
        return format_linha(self.linha)

    @property
    def kind_label(self) -> str:
        return 'Bank boleto' if self.kind == 'bank' else 'Utility/tax bill'

    def as_dict(self) -> dict:
        return {
            'barcode': self.barcode,
            'linha': self.linha,
            'formatted': self.formatted,
            'kind': self.kind,
            'amount': str(self.amount) if self.amount is not None else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'segment': self.segment,
        }


def _due_date(factor: int, today: date) -> Optional[date]:
    """Resolve a due date factor to the nearer of the dates it can mean."""
    if factor == 0:
        return None
    candidates = [_FACTOR_BASE + timedelta(days=factor)]
    if factor >= 1000:
        candidates.append(_FACTOR_RESTART + timedelta(days=factor - 1000))
    return min(candidates, key=lambda d: abs((d - today).days))


def _amount(digits: str) -> Optional[Decimal]:
    cents = int(digits)
    return Decimal(cents).scaleb(-2) if cents else None


def decode(barcode: str, today: Optional[date] = None) -> BoletoInfo:
    """
    Read the payment details out of a valid barcode. `today` anchors the due date
    factor, which repeats every 9000 days; it defaults to the current date.
    """
    if not is_valid_barcode(barcode):
        raise ValueError("not a valid boleto barcode")
    linha = barcode_to_linha(barcode)

    if barcode[0] != '8':
        return BoletoInfo(
            barcode=barcode,
            linha=linha,
            kind='bank',
            amount=_amount(barcode[9:19]),
            due_date=_due_date(int(barcode[5:9]), today or date.today()),
            segment=None,
        )

    # Value identifiers 6 and 8 carry the amount in reais; 7 and 9 carry a
    # reference quantity (e.g. an index) that is not money.
    return BoletoInfo(
        barcode=barcode,
        linha=linha,
        kind='arrecadacao',
        amount=_amount(barcode[4:15]) if barcode[2] in '68' else None,
        due_date=None,
        segment=_SEGMENTS.get(barcode[1]),
    )
