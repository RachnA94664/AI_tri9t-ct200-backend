from app.services.tree_builder import RawBlock, build_tree

def blocks_from_pairs(pairs):
    return [RawBlock(text=t, size=s, bold=b, order_index=i)
            for i, (t, s, b) in enumerate(pairs)]


def test_multilevel_numbering_2_1_1_1_parents_correctly():
    """2.1.1.1 must attach under 2.1, not get flattened to level 2 or
    mistaken for a table header despite identical font (bold, size 11)."""
    pairs = [
        ("2. Physical and Electrical Specifications", 16.5, True),
        ("2.1 General Specifications", 12.9, True),
        ("Parameter", 11.0, True),          # table header — must NOT match heading regex
        ("Value", 11.0, True),
        ("2.1.1.1 Battery Life Under Typical Use", 11.0, True),
        ("Under typical use...", 11.0, False),
    ]
    root = build_tree(blocks_from_pairs(pairs), "Doc Title")
    sec2 = root.children[0]
    sec2_1 = sec2.children[0]
    assert sec2_1.heading_number == "2.1"
    assert len(sec2_1.children) == 1
    battery = sec2_1.children[0]
    assert battery.heading_number == "2.1.1.1"
    assert battery.level == 4
    assert battery.parent is sec2_1


def test_out_of_order_siblings_3_4_before_3_3_parent_by_number_not_stream():
    """3.4 appears physically before 3.3 in the real PDF. Parenting must
    use the numeric prefix, not 'whichever heading came last in the stream'."""
    pairs = [
        ("3. Device Operation", 16.5, True),
        ("3.1 Powering On", 12.9, True),
        ("some text", 11.0, False),
        ("3.4 Auto Shutoff", 12.9, True),
        ("shutoff text", 11.0, False),
        ("3.3 Result Display", 12.9, True),
        ("display text", 11.0, False),
    ]
    root = build_tree(blocks_from_pairs(pairs), "Doc Title")
    sec3 = root.children[0]
    numbers = [c.heading_number for c in sec3.children]
    assert set(numbers) == {"3.1", "3.4", "3.3"}
    # both correctly parented under section 3 despite being out of numeric order
    for c in sec3.children:
        assert c.parent is sec3
    # order_index preserves physical/reading order for faithful rendering
    order_indices = [c.order_index for c in sec3.children]
    assert order_indices == sorted(order_indices)


def test_duplicate_heading_text_gets_distinct_ids_and_correct_parents():
    """Synthetic case: the assignment requires this even though v1 doesn't
    happen to contain a literal duplicate — prove the numbering-based
    parenting doesn't rely on heading TEXT being unique."""
    pairs = [
        ("1. Device Overview", 16.5, True),
        ("1.1 Error Codes", 12.9, True),   # duplicate text, different number
        ("text a", 11.0, False),
        ("2. Troubleshooting", 16.5, True),
        ("2.1 Error Codes", 12.9, True),   # same heading_text, different parent
        ("text b", 11.0, False),
    ]
    root = build_tree(blocks_from_pairs(pairs), "Doc Title")
    first_error_codes = root.children[0].children[0]
    second_error_codes = root.children[1].children[0]
    assert first_error_codes.heading_text == second_error_codes.heading_text == "Error Codes"
    assert first_error_codes.heading_number == "1.1"
    assert second_error_codes.heading_number == "2.1"
    assert first_error_codes.parent is not second_error_codes.parent
    # a naive parser keying nodes by heading_text alone would collide these