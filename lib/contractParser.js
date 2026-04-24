/**
 * Extracts structured data from raw contract text.
 * Used when users paste contract text directly.
 */

export function parseContractText(text) {
  const result = {
    title: '',
    vendor: '',
    startDate: null,
    endDate: null,
    renewalNotice: null,
    contractValue: null,
    autoRenews: false,
    notes: '',
  };

  const lines = text.split('\n');

  // Try to extract vendor from first few lines
  for (const line of lines.slice(0, 10)) {
    const vendorMatch = line.match(/(?:vendor|supplier|party|between|with)\s*[:\-–]?\s*(.+)/i);
    if (vendorMatch) {
      result.vendor = vendorMatch[1].trim().slice(0, 80);
      break;
    }
  }

  // Extract dates — multiple patterns
  const datePatterns = [
    /(?:effective|start|commencement)\s+date[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})/i,
    /(?:from|beginning|dated)\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})/i,
  ];
  const endDatePatterns = [
    /(?:expir|terminat|end)\w*\s+date[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})/i,
    /(?:through|until|to)\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})/i,
    /(?:expires?|renewal)\s+(?:on\s+)?([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})/i,
  ];

  for (const pattern of datePatterns) {
    const m = text.match(pattern);
    if (m) {
      const parsed = new Date(m[1]);
      if (!isNaN(parsed)) {
        result.startDate = parsed.toISOString().split('T')[0];
        break;
      }
    }
  }

  for (const pattern of endDatePatterns) {
    const m = text.match(pattern);
    if (m) {
      const parsed = new Date(m[1]);
      if (!isNaN(parsed)) {
        result.endDate = parsed.toISOString().split('T')[0];
        break;
      }
    }
  }

  // Extract monetary values
  const valueMatch = text.match(/(?:total|contract)\s+(?:value|amount|price)[:\s]+\$?([\d,]+(?:\.\d{2})?)/i)
    || text.match(/\$\s*([\d,]+(?:\.\d{2})?)\s+(?:per year|annually|total)/i);
  if (valueMatch) {
    result.contractValue = parseFloat(valueMatch[1].replace(/,/g, ''));
  }

  // Extract renewal notice period
  const noticeMatch = text.match(/(\d+)[\s-]+(?:days?|business days?)[\s]+(?:prior|before|advance|written\s+notice)/i)
    || text.match(/(?:notice|notify)\s+(?:at least\s+)?(\d+)\s+days?/i);
  if (noticeMatch) {
    result.renewalNotice = parseInt(noticeMatch[1], 10);
  }

  // Auto-renewal detection
  if (/auto[\s-]?renew|automatic(?:ally)?\s+renew|evergreen/i.test(text)) {
    result.autoRenews = true;
  }

  // Use first non-empty substantial line as title if none found
  if (!result.title) {
    const titleLine = lines.find(l => l.trim().length > 10 && l.trim().length < 100);
    result.title = titleLine ? titleLine.trim().slice(0, 100) : 'Imported Contract';
  }

  return result;
}
