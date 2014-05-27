import io

def Parse(fileBuffer):
	## fileBuffer should contain the binary contents of the config file
	## this could be ascii, or encoded text in some ascii compatible encoding
	## we don't care about encoding details for commented lines, but stuff outside of comments should only contain printable ascii characters
	## returned keys are unicode strings with contents in ascii
	assert type(fileBuffer) is type(b'')
	f = io.StringIO(fileBuffer.decode('ascii', errors='ignore'), newline=None)
	result = {}
	for line in f:
		assert type(line) is type(b''.decode())
		stripped = line.strip()
		if stripped.startswith('#'):
			continue
		parts = stripped.split('=')
		assert len(parts) == 2
		parts[0] = parts[0].strip()
		parts[1] = parts[1].strip()
		result[parts[0]] = parts[1]
	return result
