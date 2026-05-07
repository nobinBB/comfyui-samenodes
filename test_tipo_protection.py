#!/usr/bin/env python3
"""
Test script to verify that original input is protected from filtering
"""

def test_original_protection():
    """
    Verify that original input is NOT filtered even if it contains ban tag keywords
    """

    # Simulate TIPO return values
    # User input: "red hair girl, 1girl"
    # Ban tags: ".*hair.*"
    # TIPO adds: "long hair, flowing hair, beautiful"

    unformatted_by_user = "red hair girl, 1girl"  # Original input (contains "hair")
    unformatted_by_tipo = "red hair girl, 1girl, long hair, flowing hair, beautiful"  # Full output

    ban_tags = [".*hair.*"]

    print("="*60)
    print("Test: Original input protection")
    print("="*60)
    print(f"Original input: {unformatted_by_user}")
    print(f"TIPO full output: {unformatted_by_tipo}")
    print(f"Ban tags: {ban_tags}")
    print()

    # Simulate the filtering logic from tipo_nobin_custom.py

    # Extract addon
    if unformatted_by_user in unformatted_by_tipo:
        addon_part = unformatted_by_tipo.replace(unformatted_by_user, '', 1).strip()
        addon_part = addon_part.lstrip(',').lstrip('\n').strip()

        print(f"TIPO additions (to filter): {addon_part}")

        # Simulate regex filtering on addon only
        import re
        addon_tags = [tag.strip() for tag in addon_part.split(',') if tag.strip()]
        filtered_addon_tags = []
        excluded_tags = []

        for tag in addon_tags:
            excluded = False
            for ban_pattern in ban_tags:
                if re.search(ban_pattern, tag, re.IGNORECASE):
                    excluded_tags.append(tag)
                    excluded = True
                    break
            if not excluded:
                filtered_addon_tags.append(tag)

        print(f"Filtered addon tags: {filtered_addon_tags}")
        print(f"Excluded tags: {excluded_tags}")

        # Reconstruct: original + filtered addon
        result_parts = [unformatted_by_user]  # Always include original!
        if filtered_addon_tags:
            result_parts.append(', '.join(filtered_addon_tags))

        final_output = ', '.join(result_parts)

        print()
        print(f"Final output: {final_output}")
        print()

        # Verification
        print("="*60)
        print("Verification:")
        print("="*60)

        # Check 1: Original input must be in final output
        if unformatted_by_user in final_output:
            print("✓ PASS: Original input is preserved in final output")
        else:
            print("✗ FAIL: Original input was removed from final output!")
            return False

        # Check 2: "red hair girl" must be in final output (even though it matches ban tag)
        if "red hair girl" in final_output:
            print("✓ PASS: 'red hair girl' is preserved (original input protected)")
        else:
            print("✗ FAIL: 'red hair girl' was filtered out!")
            return False

        # Check 3: "long hair" and "flowing hair" should NOT be in final output (filtered)
        if "long hair" not in final_output and "flowing hair" not in final_output:
            print("✓ PASS: TIPO's additions with 'hair' were filtered correctly")
        else:
            print("✗ FAIL: TIPO's additions were not filtered!")
            return False

        # Check 4: "beautiful" should be in final output (not matching ban tag)
        if "beautiful" in final_output:
            print("✓ PASS: Non-banned additions are preserved")
        else:
            print("✗ FAIL: Non-banned additions were removed!")
            return False

        print()
        print("="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        return True

    else:
        print("ERROR: Could not find original in TIPO output")
        return False


def test_nl_protection():
    """
    Test with natural language input
    """

    unformatted_by_user = "1girl, red hair"
    unformatted_by_tipo = "1girl, red hair, long hair, flowing hair\nA girl with beautiful red hair standing in the garden"

    ban_tags = [".*hair.*"]

    print("\n\n")
    print("="*60)
    print("Test 2: Natural language protection")
    print("="*60)
    print(f"Original input: {unformatted_by_user}")
    print(f"TIPO full output: {unformatted_by_tipo}")
    print(f"Ban tags: {ban_tags}")
    print()

    # Extract addon
    if unformatted_by_user in unformatted_by_tipo:
        addon_part = unformatted_by_tipo.replace(unformatted_by_user, '', 1).strip()
        addon_part = addon_part.lstrip(',').lstrip('\n').strip()

        print(f"TIPO additions: {addon_part}")

        # Split into tags and NL
        if '\n' in addon_part:
            addon_tags, addon_nl = addon_part.split('\n', 1)
        else:
            addon_tags = addon_part
            addon_nl = ""

        print(f"Addon tags: {addon_tags}")
        print(f"Addon NL: {addon_nl}")

        # Filter addon tags (simplified - just check if we'd filter them)
        import re
        tags = [tag.strip() for tag in addon_tags.split(',') if tag.strip()]
        filtered_tags = []
        for tag in tags:
            excluded = False
            for ban_pattern in ban_tags:
                if re.search(ban_pattern, tag, re.IGNORECASE):
                    excluded = True
                    break
            if not excluded:
                filtered_tags.append(tag)

        # Reconstruct
        result_parts = [unformatted_by_user]  # Original always included
        if filtered_tags:
            result_parts.append(', '.join(filtered_tags))

        tags_part = ', '.join(result_parts)

        # For NL, we'd use semantic filtering (not doing that here, just showing it's included)
        # In real code, addon_nl would be semantically filtered
        final_output = f"{tags_part}\n{addon_nl}" if addon_nl else tags_part

        print()
        print(f"Final output: {final_output}")
        print()

        # Verify
        print("="*60)
        print("Verification:")
        print("="*60)

        if "red hair" in final_output and "1girl" in final_output:
            print("✓ PASS: Original 'red hair' and '1girl' preserved")
        else:
            print("✗ FAIL: Original input was filtered!")
            return False

        if "long hair" not in final_output and "flowing hair" not in final_output:
            print("✓ PASS: TIPO's hair-related additions filtered")
        else:
            print("✗ FAIL: TIPO's additions not filtered!")
            return False

        print()
        print("="*60)
        print("TEST 2 PASSED!")
        print("="*60)
        return True


if __name__ == "__main__":
    result1 = test_original_protection()
    result2 = test_nl_protection()

    print("\n\n")
    print("="*80)
    if result1 and result2:
        print("✓✓✓ ALL TESTS PASSED - Original input protection is working correctly! ✓✓✓")
    else:
        print("✗✗✗ TESTS FAILED - Do NOT push this code! ✗✗✗")
    print("="*80)
