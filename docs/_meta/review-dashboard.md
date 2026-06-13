# Review Dashboard

This is the editorial queue for restricted extraction work. It is generated from review metadata only and intentionally omits OCR/source-text snippets.

<div class="ah-metric-grid">
<div class="ah-metric-card">
  <div class="ah-metric-label">Boundary Review</div>
  <div class="ah-metric-value">27</div>
</div>
<div class="ah-metric-card">
  <div class="ah-metric-label">Content Separation</div>
  <div class="ah-metric-value">2</div>
</div>
<div class="ah-metric-card">
  <div class="ah-metric-label">Layout Review</div>
  <div class="ah-metric-value">92</div>
</div>
<div class="ah-metric-card">
  <div class="ah-metric-label">Source Notes</div>
  <div class="ah-metric-value">22</div>
</div>
<div class="ah-metric-card">
  <div class="ah-metric-label">General Review</div>
  <div class="ah-metric-value">0</div>
</div>
</div>

## Review Workbench

<div class="ah-review-grid">
<section class="ah-review-card warn">
  <div class="ah-review-card-kicker">27 pages</div>
  <h3>Boundary Review</h3>
  <p>Confirm thinker and work boundaries before assembling public-facing drafts.</p>
  <p><strong>Start:</strong> <code>136</code>, <code>159</code>, <code>160</code>, <code>163</code>, <code>164</code>, <code>165</code>, <code>166</code>, <code>177</code>, <code>178</code>, <code>179</code>, <code>180</code>, <code>189</code> +15 more</p>
</section>
<section class="ah-review-card warn">
  <div class="ah-review-card-kicker">2 pages</div>
  <h3>Content Separation</h3>
  <p>Keep excerpt text, source notes, and bibliography material in separate template sections.</p>
  <p><strong>Start:</strong> <code>72</code>, <code>199</code></p>
</section>
<section class="ah-review-card neutral">
  <div class="ah-review-card-kicker">92 pages</div>
  <h3>Layout Review</h3>
  <p>Confirm multi-column reading order before any summary or excerpt curation.</p>
  <p><strong>Start:</strong> <code>73</code>, <code>79</code>, <code>80</code>, <code>82</code>, <code>83</code>, <code>84</code>, <code>86</code>, <code>90</code>, <code>91</code>, <code>92</code>, <code>93</code>, <code>94</code> +80 more</p>
</section>
<section class="ah-review-card neutral">
  <div class="ah-review-card-kicker">22 pages</div>
  <h3>Source Notes</h3>
  <p>Move source footnotes into Source Notes without converting them into Markdown footnotes.</p>
  <p><strong>Start:</strong> <code>74</code>, <code>98</code>, <code>99</code>, <code>126</code>, <code>185</code>, <code>190</code>, <code>191</code>, <code>192</code>, <code>194</code>, <code>204</code>, <code>213</code>, <code>218</code> +10 more</p>
</section>
</div>

## How To Use This Page

- Review boundary pages first; they can affect thinker grouping and page inventory.
- Check content-separation pages before excerpt curation so bibliography and notes stay out of excerpt cards.
- Review multi-column reading order before asking an agent to summarize or quote from those pages.
- Normalize source-note pages into `Source Notes`; do not convert source notes into Markdown footnotes.

## Source Scope

| Field | Value |
| --- | --- |
| Source ID | `norton-theory-criticism` |
| Classified source pages | `71-267` |
| Review queue rows | `143` |
| Review queue file | `work/review/norton-theory-criticism/page-records-needing-review.csv` |
| Generated at | `2026-06-13T02:33:20Z` |
| Git commit | `de009a1` |
| Script version | `1` |
| Output path | `docs/_meta/review-dashboard.md` |

## Review Reasons

| Reason | Pages |
| --- | ---: |
| multi_column_layout | 95 |
| source_notes_detected | 88 |
| transition_from_previous_author | 23 |
| layout_review_required | 6 |
| mixed_excerpt_and_bibliography | 2 |
| author_boundary_without_life_dates | 2 |
| transition_from_previous_work | 2 |

## Thinkers Needing Review

| Thinker | Pages |
| --- | ---: |
| Plato | 29 |
| Aristotle | 23 |
| Longinus | 19 |
| Moses Maimonides | 15 |
| Horace | 14 |
| Quintilian | 10 |
| Hugh of St. Victor | 10 |
| Augustine of Hippo | 9 |
| Plotinus | 7 |
| Macrobius | 4 |
| Gorgias of Leontini | 3 |

## Boundary Review

| Page | Thinker | Work | Reasons | Restricted page record |
| ---: | --- | --- | --- | --- |
| 136 | Aristotle | Poetics | author_boundary_without_life_dates;multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0136.md |
| 159 | Aristotle | Rhetoric, Book I, Chapter 2 | transition_from_previous_work | work/page-records/norton-theory-criticism/page_0159.md |
| 160 | Aristotle | Rhetoric, Book I, Chapter 2 | transition_from_previous_work | work/page-records/norton-theory-criticism/page_0160.md |
| 163 | Horace | Horace | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0163.md |
| 164 | Horace |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0164.md |
| 165 | Horace |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0165.md |
| 166 | Horace |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0166.md |
| 177 | Longinus |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0177.md |
| 178 | Longinus |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0178.md |
| 179 | Longinus |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0179.md |
| 180 | Longinus | On Sublimity 1 | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0180.md |
| 189 | Longinus | On Sublimity | author_boundary_without_life_dates;multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0189.md |
| 227 | Augustine of Hippo |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0227.md |
| 228 | Augustine of Hippo |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0228.md |
| 229 | Augustine of Hippo |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0229.md |
| 230 | Augustine of Hippo | On Christian Doctrine I | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0230.md |
| 238 | Macrobius |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0238.md |
| 239 | Macrobius | Macrobius | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0239.md |
| 240 | Macrobius | Commentary on the Dream of Scipiol | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0240.md |
| 243 | Hugh of St. Victor |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0243.md |
| 244 | Hugh of St. Victor |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0244.md |
| 245 | Hugh of St. Victor |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0245.md |
| 246 | Hugh of St. Victor | The Didascalicon 1 | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0246.md |
| 253 | Moses Maimonides |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0253.md |
| 254 | Moses Maimonides |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0254.md |
| 255 | Moses Maimonides |  | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0255.md |
| 256 | Moses Maimonides | The Guide of the Perplexed! | transition_from_previous_author | work/page-records/norton-theory-criticism/page_0256.md |

## Content Separation

| Page | Thinker | Work | Reasons | Restricted page record |
| ---: | --- | --- | --- | --- |
| 72 | Gorgias of Leontini | Encomium of Helen | mixed_excerpt_and_bibliography;multi_column_layout | work/page-records/norton-theory-criticism/page_0072.md |
| 199 | Quintilian | Institutio Oratoria | mixed_excerpt_and_bibliography | work/page-records/norton-theory-criticism/page_0199.md |

## Layout Review

| Page | Thinker | Work | Reasons | Restricted page record |
| ---: | --- | --- | --- | --- |
| 73 | Gorgias of Leontini | Encomium of Helen | multi_column_layout | work/page-records/norton-theory-criticism/page_0073.md |
| 79 | Plato | Ion | multi_column_layout | work/page-records/norton-theory-criticism/page_0079.md |
| 80 | Plato | Ion | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0080.md |
| 82 | Plato | Ion | multi_column_layout | work/page-records/norton-theory-criticism/page_0082.md |
| 83 | Plato | Ion | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0083.md |
| 84 | Plato | Ion | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0084.md |
| 86 | Plato | Ion | multi_column_layout | work/page-records/norton-theory-criticism/page_0086.md |
| 90 | Plato | Ion | multi_column_layout | work/page-records/norton-theory-criticism/page_0090.md |
| 91 | Plato | Republic, Book II | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0091.md |
| 92 | Plato | Republic, Book II | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0092.md |
| 93 | Plato | Republic, Book II | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0093.md |
| 94 | Plato | Republic, Book II | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0094.md |
| 96 | Plato | Republic, Book II | layout_review_required;multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0096.md |
| 97 | Plato | Republic, Book II | layout_review_required;multi_column_layout | work/page-records/norton-theory-criticism/page_0097.md |
| 101 | Plato | Republic, Book III | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0101.md |
| 102 | Plato | Republic, Book III | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0102.md |
| 106 | Plato | Republic, Book III | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0106.md |
| 107 | Plato | Republic, Book VII | layout_review_required;multi_column_layout | work/page-records/norton-theory-criticism/page_0107.md |
| 110 | Plato | Republic, Book X | multi_column_layout | work/page-records/norton-theory-criticism/page_0110.md |
| 111 | Plato | Republic, Book X | layout_review_required;multi_column_layout | work/page-records/norton-theory-criticism/page_0111.md |
| 114 | Plato | Republic, Book X | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0114.md |
| 118 | Plato | Republic, Book X | multi_column_layout | work/page-records/norton-theory-criticism/page_0118.md |
| 119 | Plato | Republic, Book X | multi_column_layout | work/page-records/norton-theory-criticism/page_0119.md |
| 121 | Plato | Republic, Book X | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0121.md |
| 123 | Plato | Phaedrus | multi_column_layout | work/page-records/norton-theory-criticism/page_0123.md |
| 125 | Plato | Phaedrus | layout_review_required;multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0125.md |
| 127 | Plato | Phaedrus | layout_review_required;multi_column_layout | work/page-records/norton-theory-criticism/page_0127.md |
| 132 | Aristotle |  | multi_column_layout | work/page-records/norton-theory-criticism/page_0132.md |
| 133 | Aristotle | Poetics | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0133.md |
| 134 | Aristotle | Poetics | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0134.md |
| 138 | Aristotle | Poetics | multi_column_layout | work/page-records/norton-theory-criticism/page_0138.md |
| 139 | Aristotle | Poetics | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0139.md |
| 141 | Aristotle | Poetics | multi_column_layout | work/page-records/norton-theory-criticism/page_0141.md |
| 142 | Aristotle | Poetics | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0142.md |
| 143 | Aristotle | Poetics | multi_column_layout | work/page-records/norton-theory-criticism/page_0143.md |
| 144 | Aristotle | Poetics | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0144.md |
| 145 | Aristotle | Poetics | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0145.md |
| 146 | Aristotle | Poetics | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0146.md |
| 147 | Aristotle | Poetics | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0147.md |
| 148 | Aristotle | Poetics | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0148.md |
| 151 | Aristotle | Poetics | multi_column_layout | work/page-records/norton-theory-criticism/page_0151.md |
| 152 | Aristotle | Poetics | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0152.md |
| 153 | Aristotle | Poetics | multi_column_layout | work/page-records/norton-theory-criticism/page_0153.md |
| 155 | Aristotle | Poetics | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0155.md |
| 157 | Aristotle | Poetics | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0157.md |
| 158 | Aristotle | Poetics | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0158.md |
| 161 | Aristotle | Rhetoric, Book II, Chapter 1 | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0161.md |
| 167 | Horace | Ars Poetica | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0167.md |
| 168 | Horace | Ars Poetica | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0168.md |
| 169 | Horace | Ars Poetica | multi_column_layout | work/page-records/norton-theory-criticism/page_0169.md |
| 170 | Horace | Ars Poetica | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0170.md |
| 171 | Horace | Ars Poetica | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0171.md |
| 172 | Horace | Ars Poetica | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0172.md |
| 173 | Horace | Ars Poetica | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0173.md |
| 174 | Horace | Ars Poetica | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0174.md |
| 175 | Horace | Ars Poetica | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0175.md |
| 176 | Horace | Ars Poetica | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0176.md |
| 182 | Longinus | On Sublimity | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0182.md |
| 183 | Longinus | On Sublimity | multi_column_layout | work/page-records/norton-theory-criticism/page_0183.md |
| 184 | Longinus | On Sublimity | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0184.md |
| 186 | Longinus | On Sublimity | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0186.md |
| 187 | Longinus | On Sublimity | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0187.md |
| 188 | Longinus | On Sublimity | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0188.md |
| 193 | Longinus | On Sublimity | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0193.md |
| 195 | Longinus | On Sublimity | multi_column_layout | work/page-records/norton-theory-criticism/page_0195.md |
| 196 | Longinus | On Sublimity | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0196.md |
| 201 | Quintilian | Institutio Oratoria | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0201.md |
| 202 | Quintilian | Institutio Oratoria | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0202.md |
| 203 | Quintilian | Institutio Oratoria | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0203.md |
| 205 | Quintilian | Institutio Oratoria | multi_column_layout | work/page-records/norton-theory-criticism/page_0205.md |
| 206 | Quintilian | Institutio Oratoria | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0206.md |
| 208 | Quintilian | Institutio Oratoria | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0208.md |
| 209 | Quintilian | Institutio Oratoria | multi_column_layout | work/page-records/norton-theory-criticism/page_0209.md |
| 212 | Quintilian | Institutio Oratoria | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0212.md |
| 216 | Plotinus | the Fifth Ennead | multi_column_layout | work/page-records/norton-theory-criticism/page_0216.md |
| 217 | Plotinus | Fifth Ennead | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0217.md |
| 234 | Augustine of Hippo | On Christian Doctrine | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0234.md |
| 242 | Macrobius | Commentary on the Dream of Scipio | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0242.md |
| 247 | Hugh of St. Victor | The Didascalicon | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0247.md |
| 248 | Hugh of St. Victor | The Didascalicon | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0248.md |
| 249 | Hugh of St. Victor | The Didascalicon | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0249.md |
| 250 | Hugh of St. Victor | The Didascalicon | multi_column_layout | work/page-records/norton-theory-criticism/page_0250.md |
| 251 | Hugh of St. Victor | The Didascalicon | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0251.md |
| 252 | Hugh of St. Victor | The Didascalicon | multi_column_layout | work/page-records/norton-theory-criticism/page_0252.md |
| 257 | Moses Maimonides | The Guide of the Perplexed | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0257.md |
| 259 | Moses Maimonides | The Guide of the Perplexed | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0259.md |
| 260 | Moses Maimonides | The Guide of the Perplexed | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0260.md |
| 261 | Moses Maimonides | The Guide of the Perplexed | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0261.md |
| 263 | Moses Maimonides | The Guide of the Perplexed | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0263.md |
| 265 | Moses Maimonides | The Guide of the Perplexed | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0265.md |
| 266 | Moses Maimonides | The Guide of the Perplexed | multi_column_layout | work/page-records/norton-theory-criticism/page_0266.md |
| 267 | Moses Maimonides | The Guide of the Perplexed | multi_column_layout;source_notes_detected | work/page-records/norton-theory-criticism/page_0267.md |

## Source Notes

| Page | Thinker | Work | Reasons | Restricted page record |
| ---: | --- | --- | --- | --- |
| 74 | Gorgias of Leontini | Encomium of Helen | source_notes_detected | work/page-records/norton-theory-criticism/page_0074.md |
| 98 | Plato | Republic, Book II | source_notes_detected | work/page-records/norton-theory-criticism/page_0098.md |
| 99 | Plato | Republic, Book III | source_notes_detected | work/page-records/norton-theory-criticism/page_0099.md |
| 126 | Plato | Phaedrus | source_notes_detected | work/page-records/norton-theory-criticism/page_0126.md |
| 185 | Longinus | On Sublimity | source_notes_detected | work/page-records/norton-theory-criticism/page_0185.md |
| 190 | Longinus | On Sublimity | source_notes_detected | work/page-records/norton-theory-criticism/page_0190.md |
| 191 | Longinus | On Sublimity | source_notes_detected | work/page-records/norton-theory-criticism/page_0191.md |
| 192 | Longinus | On Sublimity | source_notes_detected | work/page-records/norton-theory-criticism/page_0192.md |
| 194 | Longinus | On Sublimity | source_notes_detected | work/page-records/norton-theory-criticism/page_0194.md |
| 204 | Quintilian | Institutio Oratoria | source_notes_detected | work/page-records/norton-theory-criticism/page_0204.md |
| 213 | Plotinus |  | source_notes_detected | work/page-records/norton-theory-criticism/page_0213.md |
| 218 | Plotinus | Fifth Ennead | source_notes_detected | work/page-records/norton-theory-criticism/page_0218.md |
| 220 | Plotinus | Fifth Ennead | source_notes_detected | work/page-records/norton-theory-criticism/page_0220.md |
| 222 | Plotinus | Fifth Ennead | source_notes_detected | work/page-records/norton-theory-criticism/page_0222.md |
| 226 | Plotinus | Fifth Ennead | source_notes_detected | work/page-records/norton-theory-criticism/page_0226.md |
| 233 | Augustine of Hippo | On Christian Doctrine | source_notes_detected | work/page-records/norton-theory-criticism/page_0233.md |
| 235 | Augustine of Hippo | The Trinity | source_notes_detected | work/page-records/norton-theory-criticism/page_0235.md |
| 236 | Augustine of Hippo | The Trinity | source_notes_detected | work/page-records/norton-theory-criticism/page_0236.md |
| 237 | Augustine of Hippo | The Trinity | source_notes_detected | work/page-records/norton-theory-criticism/page_0237.md |
| 258 | Moses Maimonides | The Guide of the Perplexed | source_notes_detected | work/page-records/norton-theory-criticism/page_0258.md |
| 262 | Moses Maimonides | The Guide of the Perplexed | source_notes_detected | work/page-records/norton-theory-criticism/page_0262.md |
| 264 | Moses Maimonides | The Guide of the Perplexed | source_notes_detected | work/page-records/norton-theory-criticism/page_0264.md |
