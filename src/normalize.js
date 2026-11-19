// Normalize any incoming payload (website form, email webhook, chat widget)
// into one clean ticket. Accepts JSON or form-encoded bodies.
const items = $input.all();
return items.map((item) => {
  const src = (item.json.body && typeof item.json.body === 'object') ? item.json.body : item.json;
  const pick = (...keys) => {
    for (const k of keys) {
      const v = src[k];
      if (v !== undefined && v !== null && String(v).trim() !== '') return String(v).trim();
    }
    return '';
  };
  const rand = Math.random().toString(36).slice(2, 6).toUpperCase();
  return {
    json: {
      ticket_id: 'T-' + Date.now().toString(36).toUpperCase() + '-' + rand,
      received_at: new Date().toISOString(),
      channel: pick('channel') || 'webhook',
      name: pick('name', 'Name', 'from_name') || 'there',
      email: pick('email', 'Email', 'from'),
      subject: pick('subject', 'Subject'),
      message: pick('message', 'Message', 'text', 'content').slice(0, 4000),
      external_id: pick('id', 'external_id', 'test_id'),
    },
  };
});
