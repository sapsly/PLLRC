with open('pip_stage2_ocr.py', 'r') as f:
    content = f.read()

old = '''        return None

    def _empty_readings'''

new = '''        # Fuzzy matching for common OCR errors
        if expected_upper == "NEUTRAL":
            for text, result in all_texts:
                text_upper = text.upper()
                if "NEUT" in text_upper or "NEUITRAL" in text_upper:
                    print("    FUZZY MATCH NEUTRAL: '{}'".format(text))
                    return (expected_value, result)

        if expected_upper == "BOX BOX":
            for text, result in all_texts:
                text_upper = text.upper()
                if "BOX" in text_upper and text_upper.count("BOX") >= 2:
                    print("    FUZZY MATCH BOX BOX: '{}'".format(text))
                    return (expected_value, result)

        if expected_upper == "0":
            for text, result in all_texts:
                text_upper = text.upper()
                if "0" in text_upper and ("LAP" in text_upper or "." in text_upper):
                    print("    NITRO ZERO MATCH: '{}' -> 0".format(text))
                    return (expected_value, result)

        if expected_upper == "BALANCED":
            for text, result in all_texts:
                text_upper = text.upper()
                if "ANCED" in text_upper or "BAL" in text_upper:
                    print("    FUZZY MATCH BALANCED: '{}'".format(text))
                    return (expected_value, result)

        if expected_upper == "BOX BOX":
            for text, result in all_texts:
                text_upper = text.upper()
                if "PIT" in text_upper and ("BOX" in text_upper or "PIT" in text_upper):
                    print("    FUZZY MATCH PIT: '{}'".format(text))
                    return (expected_value, result)

        return None

    def _empty_readings'''

content = content.replace(old, new)

with open('pip_stage2_ocr.py', 'w') as f:
    f.write(content)

print('Done')