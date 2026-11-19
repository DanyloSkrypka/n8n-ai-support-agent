// Parse Claude's JSON answer. Any problem -> throw, and the error output
// routes the ticket to the rules-based classifier instead.
const res = $input.first().json;
if (res.stop_reason === 'refusal') throw new Error('AI refused');
const textBlock = (res.content || []).find((b) => b.type === 'text');
if (!textBlock) throw new Error('No text block in AI response');
const raw = textBlock.text.trim();
const start = raw.indexOf('{');
const end = raw.lastIndexOf('}');
const parsed = JSON.parse(raw.slice(start, end + 1));
const allowed = ['question', 'order', 'complaint', 'spam'];
if (!allowed.includes(parsed.category)) throw new Error('Unknown category: ' + parsed.category);
return [{
  json: {
    category: parsed.category,
    confidence: Math.max(0, Math.min(1, Number(parsed.confidence) || 0.5)),
    faq_id: parsed.faq_id || null,
    summary: parsed.summary || '',
    classifier: 'ai:' + (res.model || 'claude'),
  },
}];
