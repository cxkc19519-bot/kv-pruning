"""A finite scalar alphabet for cross-backend adapter checks, not model BPE."""


def validate_contract(contract):
    expected = list(range(128)) + [0xA2, 0xE9, 0x20AC, 0x4E2D, 0x1F600]
    assert contract['codepoints'] == expected
    assert contract['eos_id'] == 133 and contract['vocab_size'] == 134
    assert contract['eos_display'] == '<|eos|>'
    assert contract['normalization'] == 'none' and contract['error_policy'] == 'reject_before_native'
    return expected


def encode(payload, contract):
    scalars = validate_contract(contract)
    if isinstance(payload, bytes):
        text = payload.decode('utf-8', errors='strict')
    elif isinstance(payload, str):
        text = payload
        text.encode('utf-8', errors='strict')
    else:
        raise TypeError('expected str or bytes')
    index = {value: token for token, value in enumerate(scalars)}
    if any(ord(ch) not in index for ch in text):
        raise ValueError('outside_finite_scalar_alphabet')
    return [index[ord(ch)] for ch in text]


def vocabulary(contract):
    return [chr(n).encode('utf-8') for n in validate_contract(contract)] + [contract['eos_display'].encode('ascii')]


class SyntheticTokenizer:
    def __init__(self, contract):
        self.contract = contract
        self.eos_token_id = contract['eos_id']
        self.bos_token_id = None
        self.tokens = vocabulary(contract)
        self.special_token_ids = [self.eos_token_id]
        self.callback_calls = 0

    def __call__(self, payload):
        self.callback_calls += 1
        return encode(payload, self.contract)
