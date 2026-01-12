import re

def extract_json(text: str) -> str:
    """
    Extract JSON string from text, handling markdown blocks, extra text, and double braces.
    
    This is particularly useful when parsing LLM responses that might include
    guidelines, conversational filler, or mimic escaped braces from prompts.
    """
    if not text:
        return ""
        
    content = text.strip()
    
    # 1. Handle markdown code blocks
    code_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
    if code_blocks:
        # Try each from last to first
        for block in reversed(code_blocks):
            cleaned = _clean_json_string(block.strip())
            try:
                import json
                json.loads(cleaned)
                return cleaned
            except:
                continue
        # Fallback to the last one
        return _clean_json_string(code_blocks[-1].strip())
    
    # 2. Find outermost braces or brackets
    starts = [i for i, c in enumerate(content) if c in '{[']
    ends = [i for i, c in enumerate(content) if c in '}]']
    
    if starts and ends:
        best_candidate = ""
        max_check = 10
        for s in starts[:max_check]:
            for e in reversed(ends[-max_check:]):
                if e > s:
                    candidate = content[s:e+1]
                    cleaned = _clean_json_string(candidate)
                    try:
                        import json
                        json.loads(cleaned)
                        return cleaned
                    except:
                        if not best_candidate or len(candidate) > len(best_candidate):
                            best_candidate = cleaned
        if best_candidate:
            return best_candidate

    return _clean_json_string(content)

def _clean_json_string(json_str: str) -> str:
    """
    Internal helper to clean common LLM artifacts from a JSON-like string.
    """
    cleaned = json_str.strip()
    
    # 1. Handle double braces {{ ... }} -> { ... }
    if cleaned.startswith('{{') and cleaned.endswith('}}'):
        cleaned = cleaned[1:-1].strip()
    
    # 2. Remove C-style comments (// or /* */)
    cleaned = re.sub(r'/\*[\s\S]*?\*/|([^\\:]|^)//.*$', r'\1', cleaned, flags=re.MULTILINE)
    
    # 3. Replace smart quotes
    cleaned = cleaned.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")
    
    # 4. Filter out garbage lines (hallucinations like ?, ?", *)
    lines = cleaned.split('\n')
    filtered_lines = []
    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            filtered_lines.append(line)
            continue
        # Keep lines that look like valid JSON parts
        if re.match(r'^[\[\]{}]*,?$', trimmed):
            filtered_lines.append(line)
            continue
        if ':' in trimmed:
            filtered_lines.append(line)
            continue
        if trimmed == ',':
            filtered_lines.append(line)
            continue
        # Drop short lines with only punctuation
        if len(trimmed) < 10 and any(c in trimmed for c in '?*!'):
            continue
        filtered_lines.append(line)
    cleaned = '\n'.join(filtered_lines)
        
    # 5. Handle trailing commas aggressively
    cleaned = re.sub(r',(\s*[\]}])', r'\1', cleaned)
    cleaned = re.sub(r',[\s\r\n\t]*,', ',', cleaned)
    
    # 6. Fix single-quoted keys and values
    cleaned = re.sub(r'([{,]\s*)\'([^\']+)\'(\s*:)', r'\1"\2"\3', cleaned)
    cleaned = re.sub(r':\s*\'([^\'"\n]+)\'(?=\s*[,}\]])', r': "\1"', cleaned)
        
    return cleaned
