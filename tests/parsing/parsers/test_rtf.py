from agentle.parsing.parse import parse

RTF_SAMPLE = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Arial;}}\n\b Bold Text\b0\par\nPlain line with unicode: \\u8212? dash\par\nEscaped quote: \'22\par }"


def test_rtf_basic_parsing(tmp_path):
    rtf_file = tmp_path / "sample.rtf"
    rtf_file.write_text(RTF_SAMPLE, encoding="latin-1")

    parsed = parse(str(rtf_file))
    assert parsed.name == "sample.rtf"
    assert len(parsed.sections) == 1
    text = parsed.sections[0].text
    # Basic expectations
    assert "Bold Text" in text
    assert "Plain line" in text
    # Unicode dash conversion (8212 -> —)
    assert "—" in text or "8212" in text  # depending on environment
    # Escaped hex 22 -> double quote
    assert '"' in text
