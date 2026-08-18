with open('app/services/advisory_service.py', 'rb') as f:
    content = f.read()

idx = content.find(b'class AdvisoryService:')
doc_end = content.find(b'"""', idx)
if doc_end >= 0:
    doc_end = content.find(b'"""', doc_end + 3)
    print('Docstring ends at', doc_end)
    method_idx = content.find(b'    async def ', doc_end)
    if method_idx == -1:
        method_idx = content.find(b'    def ', doc_end)
    if method_idx >= 0:
        print('First class method at byte', method_idx)
        for i in range(max(0, method_idx-10), min(method_idx+60, len(content))):
            b = content[i]
            char = chr(b) if 32 <= b <= 126 else '.'
            if b in (9, 10, 13, 32):
                print(f'{i}: 0x{b:02x} ({chr(b)})')
            else:
                print(f'{i}: 0x{b:02x} {chr(b)}')