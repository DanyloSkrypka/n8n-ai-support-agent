// Pick the answer from the knowledge base and decide who handles the ticket.
// Replies are built ONLY from the FAQ file - the AI never invents policies.
const msg = $('Normalize message').first().json;
const kb = ((j) => j.data && j.data.faqs ? j.data : j)($('Parse FAQ file').first().json);
const cls = $input.first().json;
const text = `${msg.subject} ${msg.message}`.toLowerCase();

// FAQ match: the AI's pick if valid, otherwise the best keyword score.
let faq = kb.faqs.find((f) => f.id === cls.faq_id) || null;
if (!faq) {
  let best = 0;
  for (const f of kb.faqs) {
    const score = f.keywords.reduce((n, k) => n + (text.includes(k.toLowerCase()) ? k.split(' ').length : 0), 0);
    if (score > best) { best = score; faq = f; }
  }
}

const hello = `Hi ${msg.name},\n\n`;
const bye = `\n\nBest regards,\n${kb.signature}\n\n${kb.ai_disclosure}`;
let reply = '';
let escalate = false;
let reason = '';
let priority = 'normal';
let status = 'auto_replied';

switch (cls.category) {
  case 'question':
    if (faq && cls.confidence >= 0.5) {
      reply = hello + faq.answer + bye;
    } else {
      reply = hello + kb.templates.unknown + bye;
      escalate = true; reason = 'no_confident_answer'; status = 'handoff_to_human';
    }
    break;
  case 'order':
    reply = hello + kb.templates.order + bye;
    status = 'order_logged';
    break;
  case 'complaint':
    reply = hello + kb.templates.complaint + bye;
    escalate = true; reason = 'complaint'; priority = 'high'; status = 'escalated';
    break;
  case 'spam':
    status = 'ignored_spam';
    break;
}

const faqId = cls.category === 'question' && faq ? faq.id : '';
return [{
  json: {
    ...msg,
    category: cls.category,
    confidence: cls.confidence,
    classifier: cls.classifier,
    faq_id: faqId,
    reply,
    escalate,
    escalation_reason: reason,
    priority,
    status,
    response: {
      ticket_id: msg.ticket_id,
      category: cls.category,
      confidence: cls.confidence,
      classifier: cls.classifier,
      faq_id: faqId || null,
      escalated: escalate,
      status,
      reply,
    },
  },
}];
