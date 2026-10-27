"""Static PBIP integrity checks; does not replace Power BI Desktop validation."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'LakehouseTableHealth.SemanticModel/definition/tables/table_health_snapshots.tmdl'
REPORT = ROOT / 'LakehouseTableHealth.Report/definition'
text = MODEL.read_text()
measures = re.findall(r"^\tmeasure '([^']+)' =", text, re.M)
columns = re.findall(r'^\tcolumn (\w+)', text, re.M)
assert len(measures) == len(set(measures)), 'Duplicate measure name'

def check_dax_expressions(source):
    """Catch known generation errors; this is not a complete DAX parser."""
    expressions = re.findall(
        r"^\tmeasure '([^']+)' =\n((?:\t\t\t[^\n]*\n)+)", source, re.M
    )
    assert len(expressions) == len(measures), 'Could not extract every measure'
    for name, expression in expressions:
        # Ignore strings and bracketed references before inspecting DAX tokens.
        code = re.sub(r'"(?:[^"]|"")*"|\[(?:[^\]]|\]\])*\]', ' ', expression)
        assert not re.match(r'\s*RETURN\b', code, re.I), f'{name}: RETURN without VAR'
        assert not re.search(r'\bSYNTAXERROR\b', code, re.I), f'{name}: error placeholder'
        stack = []
        for char in code:
            if char in '({':
                stack.append(char)
            elif char in ')}':
                assert stack and stack.pop() == {')': '(', '}': '{'}[char], f'{name}: delimiter mismatch'
        assert not stack, f'{name}: unclosed delimiter'
        for variable in re.findall(r'\bVAR\s+(\w+)\s*=', code, re.I):
            assert variable.startswith('__'), f'{name}: use __ prefix to avoid reserved variable names'

check_dax_expressions(text)
for number, line in enumerate(text.splitlines(), 1):
    assert line.count('"') % 2 == 0, f'Unbalanced DAX string at line {number}'
for path in ROOT.rglob('*.json'):
    json.loads(path.read_text())
page = json.loads((REPORT / 'pages/health/page.json').read_text())
visuals = []
for path in sorted((REPORT / 'pages/health/visuals').glob('*/visual.json')):
    visual = json.loads(path.read_text())
    assert visual['name'] == path.parent.name
    position = visual['position']
    assert isinstance(position['tabOrder'], int)
    assert 0 <= position['x'] <= page['width'] - position['width']
    assert 0 <= position['y'] <= page['height'] - position['height']
    for role in visual['visual']['query']['queryState'].values():
        for projection in role['projections']:
            for kind, field in projection['field'].items():
                assert field['Property'] in (measures if kind == 'Measure' else columns), field
    visuals.append(visual)
for i, left in enumerate(visuals):
    for right in visuals[i + 1:]:
        a, b = left['position'], right['position']
        overlaps = (a['x'] < b['x'] + b['width'] and b['x'] < a['x'] + a['width']
                    and a['y'] < b['y'] + b['height'] and b['y'] < a['y'] + a['height'])
        assert not overlaps, (left['name'], right['name'])
print(f'PASS: {len(visuals)} visuals; {len(measures)} measures; JSON, bounds, overlaps, bindings, and string delimiters.')
