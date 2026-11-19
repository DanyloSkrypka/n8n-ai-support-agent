// Build the Claude Messages API request. The API key is NOT here:
// the HTTP node reads it from the ANTHROPIC_API_KEY environment variable.
const msg = $('Normalize message').first().json;
const kb = ((j) => j.data && j.data.faqs ? j.data : j)($('Parse FAQ file').first().json);
const faqList = kb.faqs.map((f) => `- ${f.id}: ${f.question}`).join('\n');

const system = [
  `You are the inbox triage assistant for ${kb.company}.`,
  'Classify the customer message into exactly one category:',
  '- question: the customer asks for information (shipping, returns, payment, tracking, sizes, warranty, contact).',
  '- order: the customer wants to buy / place / change an order or asks for a quote.',
  '- complaint: the customer is unhappy (damaged, late, wrong item, bad service) or demands a refund.',
  '- spam: unsolicited marketing, SEO/crypto offers, phishing, gibberish.',
  'If it is a question, pick the best matching FAQ id from this list, or null if none fits:',
  faqList,
  'Return only JSON with keys: category, confidence (0-1), faq_id, summary (max 15 words).',
].join('\n');

const request = {
  model: $env.AI_MODEL || 'claude-opus-5-5',
  max_tokens: 2048,
  system,
  output_config: {
    effort: 'low',
    format: {
      type: 'json_schema',
      schema: {
        type: 'object',
        additionalProperties: false,
        required: ['category', 'confidence', 'faq_id', 'summary'],
        properties: {
          category: { type: 'string', enum: ['question', 'order', 'complaint', 'spam'] },
          confidence: { type: 'number' },
          faq_id: { type: ['string', 'null'] },
          summary: { type: 'string' },
        },
      },
    },
  },
  messages: [
    { role: 'user', content: `Subject: ${msg.subject || '(none)'}\nFrom: ${msg.name} <${msg.email}>\n\n${msg.message}` },
  ],
};
return [{ json: { request } }];
