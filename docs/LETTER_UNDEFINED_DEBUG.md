# Debugging "undefined" in Letter Generation

## Problem

Frontend shows "undefined" after generating a letter, but backend is working correctly.

## Backend Verification ✅

I tested the backend and confirmed:
- ✅ All placeholders are replaced correctly
- ✅ No "undefined" appears in letter_content
- ✅ API returns proper JSON with all fields

**Backend Response Example:**
```json
{
  "letter_id": 1,
  "letter_content": "IBU PEJABAT\nSURUHANJAYA PENCEGAHAN RASUAH MALAYSIA\n...",
  "letter_type": "rujuk_jabatan",
  "generated_at": "2025-10-31T17:30:00.123456",
  "complaint_id": 45
}
```

---

## Frontend Debugging Steps

### Step 1: Check Console for Errors

Open browser DevTools (F12) and check Console tab for errors.

```javascript
// In your letter generation function
console.log('=== LETTER GENERATION DEBUG ===');
console.log('Request body:', requestBody);

fetch(`/complaints/${complaintId}/letters/generate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(requestBody)
})
.then(response => {
  console.log('Response status:', response.status);
  console.log('Response headers:', response.headers);
  return response.json();
})
.then(data => {
  console.log('=== RESPONSE DATA ===');
  console.log('Full response:', data);
  console.log('letter_content exists?', 'letter_content' in data);
  console.log('letter_content type:', typeof data.letter_content);
  console.log('letter_content length:', data.letter_content?.length);
  console.log('First 100 chars:', data.letter_content?.substring(0, 100));

  // Check if data.letter_content is actually the string "undefined"
  if (data.letter_content === 'undefined') {
    console.error('❌ letter_content is the string "undefined"');
  }

  // Check if data.letter_content is JavaScript undefined
  if (data.letter_content === undefined) {
    console.error('❌ letter_content is JavaScript undefined');
  }

  // Display the letter
  displayLetter(data.letter_content);
})
.catch(error => {
  console.error('Error:', error);
});
```

### Step 2: Check How You're Displaying the Letter

**Problem Pattern 1: Accessing wrong property**
```javascript
// ❌ WRONG
displayLetter(result.content);  // There's no "content" field
displayLetter(result.letter);   // There's no "letter" field

// ✅ CORRECT
displayLetter(result.letter_content);  // Use "letter_content"
```

**Problem Pattern 2: Template literal with undefined variable**
```javascript
// ❌ WRONG - If letterContent is undefined
document.getElementById('letterDisplay').innerHTML = `
  <pre>${letterContent}</pre>
`;
// This will show "undefined" in the HTML

// ✅ CORRECT - Check first
if (result.letter_content) {
  document.getElementById('letterDisplay').innerHTML = `
    <pre>${result.letter_content}</pre>
  `;
} else {
  console.error('letter_content is missing from response');
}
```

**Problem Pattern 3: Wrong variable name**
```javascript
// ❌ WRONG
fetch(...).then(data => {
  // You're using 'response' but the parameter is 'data'
  showLetter(response.letter_content);
});

// ✅ CORRECT
fetch(...).then(data => {
  showLetter(data.letter_content);
});
```

### Step 3: Check Network Tab

1. Open DevTools → Network tab
2. Generate a letter
3. Find the POST request to `/complaints/45/letters/generate`
4. Click on it
5. Go to "Response" tab
6. Check if `letter_content` is actually there

**If letter_content is there in Network tab but shows as undefined in your code:**
- You have a JavaScript variable issue
- Check variable names carefully

**If letter_content is NOT in Network tab:**
- Backend error (but we verified it works)
- Check if you're calling the right endpoint

---

## Common Causes and Fixes

### Cause 1: Typo in Property Name

```javascript
// ❌ WRONG
console.log(result.lettercontent);   // Missing underscore
console.log(result.letter_Content);  // Wrong capitalization
console.log(result.content);         // Wrong property

// ✅ CORRECT
console.log(result.letter_content);  // Exact match
```

### Cause 2: Async/Await Issue

```javascript
// ❌ WRONG - letterData might be undefined
let letterData;
fetch(...).then(data => {
  letterData = data;
});
console.log(letterData.letter_content); // undefined! Async hasn't finished

// ✅ CORRECT - Wait for promise
async function generateLetter() {
  const response = await fetch(...);
  const letterData = await response.json();
  console.log(letterData.letter_content); // Now it works
}
```

### Cause 3: Displaying Before Data Arrives

```javascript
// ❌ WRONG
function generateLetter() {
  fetch(...).then(data => {
    letterContent = data.letter_content;
  });

  // This runs BEFORE fetch completes!
  displayLetter(letterContent); // undefined!
}

// ✅ CORRECT
function generateLetter() {
  fetch(...).then(data => {
    letterContent = data.letter_content;
    displayLetter(letterContent); // Inside the .then()
  });
}
```

### Cause 4: React State Update Issue

```javascript
// ❌ WRONG - React state might not update immediately
const [letter, setLetter] = useState('');

const generateLetter = async () => {
  const result = await fetch(...);
  const data = await result.json();
  setLetter(data.letter_content);

  // This might show old state (empty string)
  console.log(letter); // undefined or ''
};

// ✅ CORRECT - Use the data directly
const generateLetter = async () => {
  const result = await fetch(...);
  const data = await result.json();
  setLetter(data.letter_content);

  // Use data.letter_content directly if you need it immediately
  displayLetterInModal(data.letter_content);
};
```

---

## Test Code to Verify Frontend

Add this to your frontend code temporarily:

```javascript
// Test function
async function testLetterGeneration() {
  try {
    const response = await fetch('http://localhost:8000/complaints/45/letters/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        letter_type: 'rujuk_jabatan',
        fields: {
          rujukan_tuan: '',
          rujukan_kami: 'SPRM. BPRM. 600-2/3/2 Jld.5(45)',
          tarikh_surat: '31 Oktober 2025',
          recipient_title: 'YBhg. Dato\',',
          recipient_name: 'Test',
          recipient_organization: 'Test Org',
          recipient_address_line1: 'Test Address',
          recipient_address_line2: '',
          recipient_address_line3: '',
          recipient_state: 'JOHOR',
          salutation: 'YBhg. Dato\',',
          subject_line: 'TEST',
          officer_title: 'Pengarah',
          officer_department: 'Test Dept',
          cc_line1: '',
          cc_line2: '',
          cc_line3: '',
          cc_line4: ''
        },
        generated_by: 'test'
      })
    });

    const data = await response.json();

    console.log('=== TEST RESULTS ===');
    console.log('Status:', response.status);
    console.log('Response keys:', Object.keys(data));
    console.log('letter_content exists?', 'letter_content' in data);
    console.log('letter_content type:', typeof data.letter_content);
    console.log('letter_content value:', data.letter_content);

    if (data.letter_content === undefined) {
      console.error('❌ PROBLEM: letter_content is undefined');
    } else if (data.letter_content === 'undefined') {
      console.error('❌ PROBLEM: letter_content is the string "undefined"');
    } else if (data.letter_content === '') {
      console.error('❌ PROBLEM: letter_content is empty string');
    } else {
      console.log('✅ SUCCESS: letter_content has value');
      console.log('Length:', data.letter_content.length);
      console.log('Preview:', data.letter_content.substring(0, 200));
    }

    return data;

  } catch (error) {
    console.error('❌ ERROR:', error);
  }
}

// Run test
testLetterGeneration();
```

Run this in your browser console and share the output.

---

## Checklist

- [ ] Open Browser DevTools (F12)
- [ ] Go to Console tab
- [ ] Run the test function above
- [ ] Check what it prints
- [ ] Look for errors in Console
- [ ] Check Network tab → find the POST request
- [ ] View the Response in Network tab
- [ ] Confirm `letter_content` is in the response
- [ ] Compare with what your code is actually using

---

## Most Likely Issue

Based on the error "shows undefined", the most likely causes are:

1. **Wrong property name** - Using `result.content` instead of `result.letter_content`
2. **Typo** - `result.lettercontent` (missing underscore)
3. **Accessing before data arrives** - Async timing issue
4. **Wrong variable** - Using wrong variable name in template

**Share your actual frontend code** (the part that generates and displays the letter) and I can pinpoint the exact issue.
