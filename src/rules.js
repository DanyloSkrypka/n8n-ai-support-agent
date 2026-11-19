// Rules-based classifier: used when no ANTHROPIC_API_KEY is set
// or when the AI call fails. Deterministic, free, works offline (EN + DE).
const msg = $('Normalize message').first().json;
const text = `${msg.subject} ${msg.message}`.toLowerCase();
const count = (patterns) => patterns.reduce((n, re) => n + (re.test(text) ? 1 : 0), 0);

const spamHits = count([
  /\b(seo|backlinks?|guest post|rank #?1|first page of google)\b/,
  /\b(crypto|bitcoin|forex|investment opportunity|double your)\b/,
  /\b(casino|lottery|you (have )?won|winner|prize|claim your)\b/,
  /\b(cheap followers|buy followers|click here|limited offer|act now)\b/,
  /(bit\.ly|tinyurl|https?:\/\/\S+\.(ru|xyz|top)\b)/,
  /\$\d{3,}|\b100% free\b|!!!/,
]) + ((text.match(/https?:\/\//g) || []).length >= 2 ? 1 : 0);

const complaintHits = count([
  /\b(complain|complaint|disappointed|unacceptable|terrible|awful|worst|horrible|furious|angry)\b/,
  /\b(broken|damaged|defective|faulty|torn|wrong (item|size|colou?r)|missing)\b/,
  /(never arrived|still (haven'?t|hasn'?t|not) (received|arrived)|been waiting|weeks? late|no one (answers|replies))/,
  /\b(refund (me|now|immediately)|money back|chargeback|lawyer|scam)\b/,
  /\b(beschwerde|kaputt|beschädigt|enttäuscht|unverschämt|frechheit)\b/,
]);

const orderHits = count([
  /\b(i('d| would) like to (order|buy|purchase)|i want to (order|buy|purchase)|place an order|can i order)\b/,
  /\b(please send me|i('ll| will) take|add to my order|quote for|bulk order|wholesale)\b/,
  /\b\d+\s?(x|pcs|pieces|units|pairs)\b/,
  /\b(ich möchte .*(bestellen|kaufen)|bestellung aufgeben|ich bestelle)\b/,
]);

const questionHits = count([
  /\?/,
  /\b(how|what|when|where|which|do you|can i|is there|is it|are there)\b/,
  /\b(wie|wann|wo|was|welche|gibt es|kann ich)\b/,
]);

let category = 'question';
let hits = questionHits;
if (spamHits >= 2) { category = 'spam'; hits = spamHits; }
else if (complaintHits >= 1) { category = 'complaint'; hits = complaintHits; }
else if (orderHits >= 1) { category = 'order'; hits = orderHits; }

const confidence = hits === 0 ? 0.35 : Math.min(0.95, 0.55 + 0.15 * hits);
return [{ json: { category, confidence: Number(confidence.toFixed(2)), faq_id: null, summary: '', classifier: 'rules' } }];
