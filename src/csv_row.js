// Turn the ticket into one CSV line (the "Google Sheets" stub).
// In production replace this + the next node with a Google Sheets "Append row" node.
const t = $input.first().json;
const cols = [t.ticket_id, t.received_at, t.channel, t.name, t.email, t.category, t.confidence,
  t.classifier, t.faq_id, t.escalate ? 'yes' : 'no', t.status, t.message, t.reply];
const esc = (v) => '"' + String(v ?? '').replace(/\r?\n/g, ' / ').replace(/"/g, '""') + '"';
const line = cols.map(esc).join(',') + '\n';
return [{
  json: t,
  binary: { data: { data: Buffer.from(line, 'utf8').toString('base64'), mimeType: 'text/csv', fileName: 'tickets.csv', fileExtension: 'csv' } },
}];
