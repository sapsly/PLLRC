with open('pip_stage2_ocr.py', 'r') as f:
    content = f.read()

old = '''    def _match_control_value(self, control_name: str, expected_value: str,
                              all_texts: List, location: ControlRowLocation) -> Optional[tuple]:
        """
        Match a control to its OCR-detected value using flexible text matching.
        """
        expected_upper = expected_value.upper() if expected_value else None
        
        if not expected_upper:
            return None
        
        # Try exact substring match first
        for text, result in all_texts:
            text_upper = text.upper()
            if expected_upper in text_upper:
                print("    MATCH {}: '{}' contains '{}'".format(control_name, text, expected_upper))
                return (text, result)
        
        # Try partial match (OCR may partially read words)
        expected_words = expected_upper.split()
        for text, result in all_texts:
            text_upper = text.upper()
            for word in expected_words:
                if len(word) >= 3 and word in text_upper:
                    print("    PARTIAL MATCH {}: '{}' contains word '{}'".format(control_name, text, word))
                    return (text, result)
            if len(expected_upper) >= 4 and expected_upper[:4] in text_upper:
                print("    PREFIX MATCH {}: '{}' contains prefix '{}'".format(control_name, text, expected_upper[:4]))
                return (text, result)
            if len(text_upper) >= 4 and text_upper in expected_upper:
                print("    REVERSE MATCH {}: '{}' is prefix of '{}'".format(control_name, text_upper, expected_upper))
                return (text, result)
        
        # Fuzzy matching for common OCR errors
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
        
        return None'''

new = '''    def _match_control_value(self, control_name: str, expected_value: str,
                              all_texts: List, location: ControlRowLocation) -> Optional[tuple]:
        """
        Match a control to its OCR-detected value using flexible text matching.
        Returns (normalized_value, result_dict) or None.
        """
        expected_upper = expected_value.upper() if expected_value else None
        
        if not expected_upper:
            return None
        
        # First pass: collect all candidate matches with their match type
        candidates = []
        
        for text, result in all_texts:
            text_upper = text.upper()
            
            # Exact substring match
            if expected_upper in text_upper:
                candidates.append(("exact", expected_value, result))
                continue
            
            # Partial word match
            expected_words = expected_upper.split()
            for word in expected_words:
                if len(word) >= 3 and word in text_upper:
                    candidates.append(("partial", expected_value, result))
                    break
            
            # Prefix match
            if len(expected_upper) >= 4 and expected_upper[:4] in text_upper:
                candidates.append(("prefix", expected_value, result))
                continue
            
            # Reverse match (OCR text is prefix of expected)
            if len(text_upper) >= 4 and text_upper in expected_upper:
                candidates.append(("reverse", expected_value, result))
                continue
        
        # Fuzzy matching for common OCR errors
        if expected_upper == "NEUTRAL":
            for text, result in all_texts:
                text_upper = text.upper()
                if "NEUT" in text_upper or "NEUITRAL" in text_upper:
                    candidates.append(("fuzzy_neutral", expected_value, result))
                    break
        
        if expected_upper == "BOX BOX":
            for text, result in all_texts:
                text_upper = text.upper()
                if "BOX" in text_upper and text_upper.count("BOX") >= 2:
                    candidates.append(("fuzzy_box", expected_value, result))
                    break
        
        if expected_upper == "0":
            for text, result in all_texts:
                text_upper = text.upper()
                if "0" in text_upper and ("LAP" in text_upper or "." in text_upper):
                    candidates.append(("fuzzy_nitro_zero", expected_value, result))
                    break
        
        if expected_upper == "BALANCED":
            for text, result in all_texts:
                text_upper = text.upper()
                if "ANCED" in text_upper or "BAL" in text_upper:
                    candidates.append(("fuzzy_balanced", expected_value, result))
                    break
        
        if expected_upper == "BOX BOX":
            for text, result in all_texts:
                text_upper = text.upper()
                if "PIT" in text_upper and ("BOX" in text_upper or "PIT" in text_upper):
                    candidates.append(("fuzzy_pit", expected_value, result))
                    break
        
        # Return best candidate (prioritize exact > partial > prefix > reverse > fuzzy)
        priority = {"exact": 0, "partial": 1, "prefix": 2, "reverse": 3, 
                    "fuzzy_neutral": 4, "fuzzy_box": 5, "fuzzy_nitro_zero": 6,
                    "fuzzy_balanced": 7, "fuzzy_pit": 8}
        
        if candidates:
            candidates.sort(key=lambda c: priority.get(c[0], 99))
            match_type, norm_val, result = candidates[0]
            print("    MATCH {} [{}] = '{}'".format(control_name, match_type, norm_val))
            return (norm_val, candidates[0][2])
        
        return None'''

content = content.replace(old, new)

with open('pip_stage2_ocr.py', 'w') as f:
    f.write(content)

print('Done')