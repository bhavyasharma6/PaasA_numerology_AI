"""
numerology.py - Numerology Calculation Engine for PaasA Numerology AI
Author: Bhavya Sharma | Enrollment: 2450850380 | MCSP-232

This module implements:
  - Chaldean Name Number calculation
  - Mulank (Driver/Birth Number) calculation
  - Bhagyank (Conductor/Life Path Number) calculation
  - Kua Number (Feng Shui) calculation
  - Lo Shu Grid generation and plane analysis
"""


# ─────────────────────────────────────────────────────────────────────────────
# Chaldean Numerology Alphabet-to-Number Mapping
# Based on ancient Chaldean system (different from Pythagorean)
# ─────────────────────────────────────────────────────────────────────────────
CHALDEAN_MAP = {
    'A': 1, 'I': 1, 'J': 1, 'Q': 1, 'Y': 1,
    'B': 2, 'K': 2, 'R': 2,
    'C': 3, 'G': 3, 'L': 3, 'S': 3,
    'D': 4, 'M': 4, 'T': 4,
    'E': 5, 'H': 5, 'N': 5, 'X': 5,
    'U': 6, 'V': 6, 'W': 6,
    'O': 7, 'Z': 7,
    'F': 8, 'P': 8,
}

# ─────────────────────────────────────────────────────────────────────────────
# Lo Shu Grid Position Mapping
# Ancient 3x3 magic square where rows/cols/diags all sum to 15
# Position: number -> (row, col)
# ─────────────────────────────────────────────────────────────────────────────
LOSHU_POSITIONS = {
    4: (0, 0), 9: (0, 1), 2: (0, 2),
    3: (1, 0), 5: (1, 1), 7: (1, 2),
    8: (2, 0), 1: (2, 1), 6: (2, 2),
}

# ─────────────────────────────────────────────────────────────────────────────
# Plane Definitions (rows and columns of Lo Shu Grid)
# ─────────────────────────────────────────────────────────────────────────────
PLANES = {
    'mental':    {'numbers': [4, 9, 2], 'axis': 'Row 1', 'meaning': 'Thinking & Intelligence'},
    'emotional': {'numbers': [3, 5, 7], 'axis': 'Row 2', 'meaning': 'Feelings & Sensitivity'},
    'practical': {'numbers': [8, 1, 6], 'axis': 'Row 3', 'meaning': 'Action & Material'},
    'thought':   {'numbers': [4, 3, 8], 'axis': 'Col 1', 'meaning': 'Planning & Ideas'},
    'will':      {'numbers': [9, 5, 1], 'axis': 'Col 2', 'meaning': 'Determination & Power'},
    'action':    {'numbers': [2, 7, 6], 'axis': 'Col 3', 'meaning': 'Execution & Results'},
}

# Descriptions for each core number
NUMBER_DESCRIPTIONS = {
    1: 'Leadership, independence, ambition, originality',
    2: 'Diplomacy, cooperation, sensitivity, balance',
    3: 'Creativity, expression, joy, communication',
    4: 'Stability, discipline, hard work, practicality',
    5: 'Freedom, change, adventure, versatility',
    6: 'Responsibility, nurturing, harmony, love',
    7: 'Wisdom, introspection, spirituality, analysis',
    8: 'Power, success, material abundance, authority',
    9: 'Compassion, completion, humanitarianism, wisdom',
}


def reduce_to_single(n: int) -> int:
    """
    Reduce a number to a single digit (1-9) by summing its digits.
    Master numbers (11, 22, 33) are reduced further in this system.

    Args:
        n: Integer to reduce
    Returns:
        Single digit integer (1-9)
    """
    while n > 9:
        n = sum(int(digit) for digit in str(n))
    return max(1, n)  # ensure at least 1


def calculate_name_number(name: str) -> int:
    """
    Calculate the Chaldean Name Number.

    Each letter of the name is mapped to its Chaldean value,
    all values are summed and reduced to a single digit.

    Args:
        name: Full name string
    Returns:
        Name number (1-9)
    """
    name_clean = name.upper().replace(' ', '')
    total = sum(CHALDEAN_MAP.get(char, 0) for char in name_clean if char.isalpha())
    return reduce_to_single(total)


def get_name_breakdown(name: str) -> dict:
    """
    Get letter-by-letter Chaldean value breakdown for the name.

    Args:
        name: Full name string
    Returns:
        Dictionary with letter values and total
    """
    breakdown = {}
    total = 0
    for char in name.upper():
        if char.isalpha():
            val = CHALDEAN_MAP.get(char, 0)
            breakdown[char] = val
            total += val
    return {
        'breakdown': breakdown,
        'raw_total': total,
        'reduced': reduce_to_single(total)
    }


def calculate_mulank(dob: str) -> int:
    """
    Calculate Mulank (Driver Number / Birth Number).

    The Mulank is the birth day reduced to a single digit.
    It represents the core personality and natural tendencies.

    Args:
        dob: Date of birth in DD-MM-YYYY format
    Returns:
        Mulank number (1-9)
    """
    day = int(dob.split('-')[0])
    return reduce_to_single(day)


def calculate_bhagyank(dob: str) -> int:
    """
    Calculate Bhagyank (Conductor Number / Life Path Number).

    The Bhagyank is calculated by summing ALL digits of the
    complete date of birth and reducing to a single digit.
    It represents the life path and destiny.

    Args:
        dob: Date of birth in DD-MM-YYYY format
    Returns:
        Bhagyank number (1-9)
    """
    digits_only = [int(d) for d in dob if d.isdigit()]
    total = sum(digits_only)
    return reduce_to_single(total)


def calculate_kua(dob: str, gender: str) -> int:
    """
    Calculate the Kua Number (Feng Shui Number).

    The Kua number is based on birth year and gender.
    Males: Kua = 11 - (sum of year digits reduced)
    Females: Kua = 4 + (sum of year digits reduced)

    Note: Kua 5 is not valid for males (becomes 1 or 2 depending on system;
    here it defaults to 1 for males).

    Args:
        dob: Date of birth in DD-MM-YYYY format
        gender: 'Male' or 'Female'
    Returns:
        Kua number (1-9)
    """
    year_str = dob.split('-')[2]
    year_sum = reduce_to_single(sum(int(d) for d in year_str))

    if gender.lower() == 'male':
        kua = reduce_to_single(11 - year_sum)
        return 1 if kua == 5 else kua
    else:
        kua = reduce_to_single(4 + year_sum)
        return kua


def extract_dob_digits(dob: str) -> list:
    """
    Extract all meaningful numerology digits from date of birth.

    Includes: mulank, bhagyank, individual day/month/year digits.
    These form the basis of the Lo Shu Grid.

    Args:
        dob: Date of birth in DD-MM-YYYY format
    Returns:
        List of significant numbers from DOB
    """
    parts = dob.split('-')
    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])

    numbers = []

    # Add day digits
    day_reduced = reduce_to_single(day)
    numbers.append(day_reduced)
    if day >= 10:
        for d in str(day):
            if int(d) > 0:
                numbers.append(int(d))

    # Add month digits
    month_reduced = reduce_to_single(month)
    numbers.append(month_reduced)
    if month >= 10:
        for d in str(month):
            if int(d) > 0:
                numbers.append(int(d))

    # Add year digits individually
    for d in str(year):
        if int(d) > 0:
            numbers.append(int(d))

    # Add bhagyank (life path)
    numbers.append(calculate_bhagyank(dob))

    return [n for n in numbers if 1 <= n <= 9]


def generate_loshu_grid(numbers: list) -> dict:
    """
    Generate the Lo Shu Grid from numerology numbers.

    Places each number in its correct grid position and
    tracks frequencies of each digit 1-9.

    Args:
        numbers: List of significant numerology numbers
    Returns:
        Dictionary with grid, present_numbers, missing_numbers, frequencies
    """
    grid = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    frequencies = {i: 0 for i in range(1, 10)}

    for n in numbers:
        if 1 <= n <= 9:
            frequencies[n] += 1
            row, col = LOSHU_POSITIONS[n]
            grid[row][col] = n

    present_numbers = sorted([n for n in range(1, 10) if frequencies[n] > 0])
    missing_numbers = sorted([n for n in range(1, 10) if frequencies[n] == 0])

    return {
        'grid': grid,
        'present_numbers': present_numbers,
        'missing_numbers': missing_numbers,
        'frequencies': frequencies,
    }


def analyze_planes(frequencies: dict) -> dict:
    """
    Analyze the six planes of the Lo Shu Grid.

    Each plane is evaluated as:
      - Weak:     0 numbers present in that plane
      - Balanced: Some numbers present (1 or 2 out of 3)
      - Strong:   All 3 numbers present

    Args:
        frequencies: Dictionary of number frequencies from grid
    Returns:
        Dictionary of plane analysis results
    """
    results = {}
    strongest = None
    max_present = -1

    for plane_name, plane_info in PLANES.items():
        nums = plane_info['numbers']
        present_count = sum(1 for n in nums if frequencies.get(n, 0) > 0)

        if present_count == 0:
            status = 'Weak'
        elif present_count == len(nums):
            status = 'Strong'
        else:
            status = 'Balanced'

        results[plane_name] = {
            'numbers': nums,
            'present': present_count,
            'total': len(nums),
            'status': status,
            'axis': plane_info['axis'],
            'meaning': plane_info['meaning'],
        }

        if present_count > max_present:
            max_present = present_count
            strongest = plane_name

    results['strongest_plane'] = strongest
    return results


def get_full_numerology(name: str, dob: str, gender: str) -> dict:
    """
    Compute the complete numerology profile for a user.

    This is the main entry point that orchestrates all calculations.

    Args:
        name:   Full name
        dob:    Date of birth (DD-MM-YYYY)
        gender: 'Male' or 'Female'
    Returns:
        Complete numerology profile dictionary
    """
    # Core numbers
    name_number = calculate_name_number(name)
    mulank = calculate_mulank(dob)
    bhagyank = calculate_bhagyank(dob)
    kua_number = calculate_kua(dob, gender)

    # Collect numbers for grid (DOB digits + all core numbers)
    dob_digits = extract_dob_digits(dob)
    all_numbers = dob_digits + [name_number, mulank, bhagyank, kua_number]

    # Grid and plane analysis
    grid_data = generate_loshu_grid(all_numbers)
    plane_data = analyze_planes(grid_data['frequencies'])

    # Number descriptions
    descriptions = {
        'name_number': NUMBER_DESCRIPTIONS.get(name_number, ''),
        'mulank': NUMBER_DESCRIPTIONS.get(mulank, ''),
        'bhagyank': NUMBER_DESCRIPTIONS.get(bhagyank, ''),
        'kua_number': NUMBER_DESCRIPTIONS.get(kua_number, ''),
    }

    return {
        'numbers': {
            'name_number': name_number,
            'mulank': mulank,
            'bhagyank': bhagyank,
            'kua_number': kua_number,
        },
        'descriptions': descriptions,
        'loshu_grid': grid_data,
        'planes': plane_data,
        'name_breakdown': get_name_breakdown(name),
    }
