# Markdown Processing for PDF Generation

This document explains how Markdown content is processed and formatted for PDF generation in the Law & Order application.

## Overview

The application uses a custom Markdown processing function (`processMarkdownForPDF`) to convert Markdown syntax to plain text with appropriate formatting before generating PDFs. This ensures that the generated PDFs have proper formatting while removing Markdown syntax characters that shouldn't appear in the final document.

## How It Works

The `processMarkdownForPDF` function is located in `src/lib/templates.ts` and performs the following operations:

1. Takes Markdown text as input (typically generated from a Handlebars template)
2. Processes various Markdown syntax elements using regular expressions
3. Returns a processed text string ready for PDF rendering

## Supported Markdown Features

The Markdown processor handles the following formatting elements:

### Headings

Headings (lines starting with `#`) are converted to uppercase text, which helps them stand out in the PDF document:

```markdown
# Heading 1
## Heading 2
```

Becomes:

```
HEADING 1
HEADING 2
```

### Emphasis

Bold and italic text markers are removed while preserving the content:

```markdown
*italic text*
**bold text**
_italic text_
__bold text__
```

Becomes:

```
italic text
bold text
italic text
bold text
```

### Lists

#### Bullet Points

Bullet points are converted to proper bullet characters (`•`):

```markdown
- Item 1
* Item 2
+ Item 3
```

Becomes:

```
• Item 1
• Item 2
• Item 3
```

#### Numbered Lists

Numbered lists keep their numbers:

```markdown
1. First item
2. Second item
```

Remains as:

```
1. First item
2. Second item
```

### Blockquotes

Blockquotes are indented with 4 spaces:

```markdown
> This is a blockquote
```

Becomes:

```
    This is a blockquote
```

### Code Blocks

Code blocks have their backticks removed:

```markdown
```javascript
function example() {
  return 'example';
}
```
```

Becomes:

```
function example() {
  return 'example';
}
```

### Inline Code

Inline code markers are removed:

```markdown
Use the `example()` function
```

Becomes:

```
Use the example() function
```

### Links

Link syntax is simplified to just the link text:

```markdown
[Visit our website](https://example.com)
```

Becomes:

```
Visit our website
```

### Tables

Tables are simplified by removing the pipe characters and header separators:

```markdown
| Name | Age |
|------|-----|
| John | 30  |
| Jane | 25  |
```

Becomes:

```
Name Age
John 30
Jane 25
```

### Horizontal Rules

Horizontal rules (`---`) are replaced with newlines for spacing:

```markdown
Text before
---
Text after
```

Becomes:

```
Text before

Text after
```

### Spacing

The processor also handles:
- Double spacing between paragraphs
- Removal of extra spaces
- Normalization of multiple newlines

## PDF Generation Process

After the Markdown is processed, the text is then used in the PDF generation process:

1. An existing letterhead PDF is loaded using `pdf-lib` (or a new document is created if no letterhead is used).
2. The processed text is prepared for drawing (e.g., basic line splitting is performed).
3. Each line is rendered onto the PDF page(s) using `pdf-lib`'s drawing functions.
4. `pdf-lib` handles page creation/management if content overflows the available space on the letterhead or subsequent pages.

## Customizing the Markdown Processing

If you need to customize how Markdown is processed, modify the `processMarkdownForPDF` function in `src/lib/templates.ts`. You can:

- Add support for additional Markdown features
- Change how specific elements are processed
- Adjust spacing or formatting preferences
- Add special handling for custom syntax

Example modification to change how headings are processed:

```typescript
// To make headings bold and uppercase instead of just uppercase
processedText = processedText.replace(/^#{1,6}\s+(.+)$/gm, (match, heading) => {
  return `**${heading.toUpperCase()}**`;
});
```

## Implementation Details

The implementation uses regular expressions for text processing rather than a full Markdown parser. This approach was chosen for simplicity and better control over the output format. The processed text is then handed off to `pdf-lib` for rendering onto the PDF.

## Future Improvements

Potential improvements to the Markdown processing could include:

1. Adding custom styling for different heading levels
2. Supporting more sophisticated table formatting
3. Handling nested lists with proper indentation
4. Adding support for images with proper placement
5. Implementing page headers and footers

## Related Files

- `src/lib/templates.ts` - Contains the `processMarkdownForPDF` function
- `src/app/api/clients/[clientId]/documents/route.ts` - Uses the processor and `pdf-lib` for document generation with letterhead.
- `src/app/api/clients/route.ts` - Uses the processor and `pdf-lib` for automatic document generation with letterhead.
- `src/templates/*.md` - Template files that contain Markdown content 