# Frontend Error Handling Guide

## Common Errors and Solutions

### 1. **Internal Server Error (500) - Invalid Complaint ID**

**Error:**
```
Failed to load resource: the server responded with a status of 500 (Internal Server Error)
:8000/complaints/0/letters
```

**Cause:** Frontend is trying to access complaint with ID = 0 (invalid)

**Solution:**
```javascript
// BEFORE (Wrong)
const complaintId = 0; // or undefined/null
fetch(`/complaints/${complaintId}/letters`);

// AFTER (Correct)
const complaintId = getComplaintIdFromUrl(); // Get from URL params
if (!complaintId || complaintId <= 0) {
  console.error('Invalid complaint ID');
  return; // Don't make API call
}

fetch(`/complaints/${complaintId}/letters`)
  .then(response => {
    if (!response.ok) {
      if (response.status === 400) {
        throw new Error('Invalid complaint ID');
      }
      if (response.status === 404) {
        throw new Error('Complaint not found');
      }
      throw new Error('Server error');
    }
    return response.json();
  })
  .catch(error => {
    console.error('Error loading letters:', error);
    // Show user-friendly error message
    showErrorToUser('Unable to load letters. Please try again.');
  });
```

### 2. **Cannot Read Properties of Null**

**Error:**
```
TypeError: Cannot read properties of null (reading 'style')
TypeError: Cannot set properties of null (setting 'innerHTML')
```

**Cause:** Trying to access DOM elements before they exist

**Solution:**

```javascript
// BEFORE (Wrong)
document.getElementById('letterHistory').innerHTML = '...'; // Element might not exist

// AFTER (Correct)
const letterHistoryElement = document.getElementById('letterHistory');
if (letterHistoryElement) {
  letterHistoryElement.innerHTML = '...';
} else {
  console.warn('Letter history element not found');
}

// OR use optional chaining
document.getElementById('letterHistory')?.innerHTML = '...';

// OR wait for DOM ready
document.addEventListener('DOMContentLoaded', () => {
  const element = document.getElementById('letterHistory');
  if (element) {
    element.innerHTML = '...';
  }
});
```

### 3. **Complaint Details Page Errors**

**Common Issues:**

#### A. Invalid Complaint ID from URL

```javascript
// Get complaint ID from URL
function getComplaintIdFromUrl() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id') || urlParams.get('complaint_id');

  // Validate
  if (!id || isNaN(id) || parseInt(id) <= 0) {
    console.error('Invalid complaint ID:', id);
    showErrorPage('Invalid complaint ID');
    return null;
  }

  return parseInt(id);
}

// Usage
const complaintId = getComplaintIdFromUrl();
if (!complaintId) {
  return; // Stop execution
}

// Now safe to load complaint
loadComplaintDetails(complaintId);
```

#### B. Load Complaint Details Safely

```javascript
async function loadComplaintDetails(complaintId) {
  try {
    // Validate ID first
    if (!complaintId || complaintId <= 0) {
      throw new Error('Invalid complaint ID');
    }

    // Show loading state
    showLoadingSpinner();

    // Fetch complaint
    const response = await fetch(`/complaints/${complaintId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Complaint not found');
      }
      throw new Error(`Server error: ${response.status}`);
    }

    const complaint = await response.json();

    // Validate response
    if (!complaint || !complaint.id) {
      throw new Error('Invalid complaint data received');
    }

    // Populate UI
    populateComplaintUI(complaint);

    // Load related data (only if complaint exists)
    await Promise.all([
      loadLetterHistory(complaintId).catch(err => {
        console.error('Error loading letters:', err);
        // Don't fail entire page if letters fail
        showLettersError('Unable to load letters');
      }),
      loadRelatedCases(complaintId).catch(err => {
        console.error('Error loading cases:', err);
        showCasesError('Unable to load related cases');
      })
    ]);

  } catch (error) {
    console.error('Error loading complaint:', error);
    showErrorPage(error.message || 'Unable to load complaint details');
  } finally {
    hideLoadingSpinner();
  }
}
```

#### C. Populate UI Safely

```javascript
function populateComplaintUI(complaint) {
  // Helper function to safely set text
  const setText = (elementId, value, fallback = 'N/A') => {
    const element = document.getElementById(elementId);
    if (element) {
      element.textContent = value || fallback;
    } else {
      console.warn(`Element not found: ${elementId}`);
    }
  };

  // Helper function to safely set HTML
  const setHTML = (elementId, html, fallback = '<p>No data</p>') => {
    const element = document.getElementById(elementId);
    if (element) {
      element.innerHTML = html || fallback;
    } else {
      console.warn(`Element not found: ${elementId}`);
    }
  };

  // Populate fields
  setText('complaint-id', complaint.id);
  setText('complaint-title', complaint.complaint_title);
  setText('complaint-status', complaint.status);
  setText('full-name', complaint.full_name, 'Anonymous');
  setText('phone-number', complaint.phone_number, 'Not provided');
  setText('email', complaint.email, 'Not provided');

  // Handle optional fields
  setText('sector', complaint.sector, 'Not classified');
  setText('sub-sector', complaint.sub_sector, 'Not classified');
  setText('classification', complaint.classification, 'Pending');

  // Handle 5W1H
  setHTML('w1h-what', complaint.w1h_what, '<i>Not generated</i>');
  setHTML('w1h-who', complaint.w1h_who, '<i>Not generated</i>');
  setHTML('w1h-when', complaint.w1h_when, '<i>Not generated</i>');
  setHTML('w1h-where', complaint.w1h_where, '<i>Not generated</i>');
  setHTML('w1h-why', complaint.w1h_why, '<i>Not generated</i>');
  setHTML('w1h-how', complaint.w1h_how, '<i>Not generated</i>');
}
```

### 4. **Case Dropdown Errors**

```javascript
async function updateCaseDropdown(complaintId) {
  const dropdown = document.getElementById('caseDropdown');

  // Check if dropdown exists
  if (!dropdown) {
    console.warn('Case dropdown element not found');
    return;
  }

  try {
    const response = await fetch('/cases');

    if (!response.ok) {
      throw new Error('Failed to load cases');
    }

    const cases = await response.json();

    // Clear existing options
    dropdown.innerHTML = '<option value="">-- Select Case --</option>';

    // Populate dropdown
    if (cases && cases.length > 0) {
      cases.forEach(caseItem => {
        const option = document.createElement('option');
        option.value = caseItem.id;
        option.textContent = `${caseItem.case_number} - ${caseItem.case_name}`;
        dropdown.appendChild(option);
      });
    } else {
      dropdown.innerHTML = '<option value="">No cases available</option>';
    }

  } catch (error) {
    console.error('Error loading cases:', error);
    dropdown.innerHTML = '<option value="">Error loading cases</option>';
    // Show error message to user
    showNotification('Unable to load cases', 'error');
  }
}
```

### 5. **Letter History Errors**

```javascript
async function loadLetterHistory(complaintId) {
  const container = document.getElementById('letterHistory');

  // Check if container exists
  if (!container) {
    console.warn('Letter history container not found');
    return;
  }

  try {
    // Validate complaint ID
    if (!complaintId || complaintId <= 0) {
      container.innerHTML = '<p class="error">Invalid complaint ID</p>';
      return;
    }

    container.innerHTML = '<p class="loading">Loading letters...</p>';

    const response = await fetch(`/complaints/${complaintId}/letters`);

    if (!response.ok) {
      if (response.status === 400) {
        throw new Error('Invalid complaint ID');
      }
      if (response.status === 404) {
        throw new Error('Complaint not found');
      }
      throw new Error('Server error');
    }

    const data = await response.json();

    // Check if letters exist
    if (!data.letters || data.letters.length === 0) {
      container.innerHTML = '<p class="no-data">No letters generated yet</p>';
      return;
    }

    // Render letters
    const lettersHTML = data.letters.map(letter => `
      <div class="letter-item">
        <h4>${letter.letter_type}</h4>
        <p>Generated: ${new Date(letter.generated_at).toLocaleString()}</p>
        <p>By: ${letter.generated_by}</p>
        <button onclick="viewLetter(${letter.id})">View</button>
      </div>
    `).join('');

    container.innerHTML = lettersHTML;

  } catch (error) {
    console.error('Error loading letter history:', error);
    container.innerHTML = `<p class="error">Error: ${error.message}</p>`;
  }
}
```

---

## Complete Example: Complaint Details Page

```javascript
// complaint-details.js

// Initialize page
document.addEventListener('DOMContentLoaded', async () => {
  // Get complaint ID from URL
  const complaintId = getComplaintIdFromUrl();

  if (!complaintId) {
    showErrorPage('Invalid complaint ID. Please check the URL.');
    return;
  }

  // Load complaint details
  await loadComplaintDetails(complaintId);
});

// Get complaint ID from URL parameters
function getComplaintIdFromUrl() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get('id') || urlParams.get('complaint_id');

  if (!id || isNaN(id) || parseInt(id) <= 0) {
    console.error('Invalid complaint ID:', id);
    return null;
  }

  return parseInt(id);
}

// Main function to load complaint details
async function loadComplaintDetails(complaintId) {
  try {
    showLoadingState();

    // Fetch complaint
    const response = await fetch(`/complaints/${complaintId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Complaint not found');
      }
      throw new Error(`Server error: ${response.status}`);
    }

    const complaint = await response.json();

    // Validate response
    if (!complaint || !complaint.id) {
      throw new Error('Invalid complaint data');
    }

    // Populate UI
    populateComplaintUI(complaint);

    // Load additional data (don't fail entire page if these fail)
    loadLetterHistory(complaintId).catch(err =>
      console.error('Letters error:', err)
    );

    loadRelatedCases(complaintId).catch(err =>
      console.error('Cases error:', err)
    );

  } catch (error) {
    console.error('Error loading complaint:', error);
    showErrorPage(error.message);
  } finally {
    hideLoadingState();
  }
}

// Safe DOM manipulation helper
function safeSetText(elementId, value, fallback = 'N/A') {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = value || fallback;
  }
}

function safeSetHTML(elementId, html, fallback = '') {
  const element = document.getElementById(elementId);
  if (element) {
    element.innerHTML = html || fallback;
  }
}

// UI state functions
function showLoadingState() {
  const loader = document.getElementById('loadingSpinner');
  if (loader) loader.style.display = 'block';

  const content = document.getElementById('complaintContent');
  if (content) content.style.display = 'none';
}

function hideLoadingState() {
  const loader = document.getElementById('loadingSpinner');
  if (loader) loader.style.display = 'none';

  const content = document.getElementById('complaintContent');
  if (content) content.style.display = 'block';
}

function showErrorPage(message) {
  const errorContainer = document.getElementById('errorContainer');
  if (errorContainer) {
    errorContainer.innerHTML = `
      <div class="error-message">
        <h2>Error</h2>
        <p>${message}</p>
        <button onclick="window.history.back()">Go Back</button>
      </div>
    `;
    errorContainer.style.display = 'block';
  }

  hideLoadingState();

  const content = document.getElementById('complaintContent');
  if (content) content.style.display = 'none';
}
```

---

## API Error Response Handling

```javascript
async function apiCall(url, options = {}) {
  try {
    const response = await fetch(url, options);

    // Handle different status codes
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      switch (response.status) {
        case 400:
          throw new Error(errorData.detail || 'Invalid request');
        case 404:
          throw new Error(errorData.detail || 'Resource not found');
        case 500:
          throw new Error('Server error. Please try again later.');
        default:
          throw new Error(`Error: ${response.status}`);
      }
    }

    return await response.json();

  } catch (error) {
    // Network error or JSON parse error
    if (error instanceof TypeError) {
      throw new Error('Network error. Please check your connection.');
    }
    throw error;
  }
}

// Usage
try {
  const complaint = await apiCall(`/complaints/${complaintId}`);
  populateComplaintUI(complaint);
} catch (error) {
  console.error('API Error:', error);
  showErrorMessage(error.message);
}
```

---

## Key Takeaways

1. **Always validate complaint ID** before making API calls
2. **Check if DOM elements exist** before accessing them
3. **Use try-catch** for all async operations
4. **Don't let partial failures break entire page** - handle letter/case loading errors gracefully
5. **Provide user-friendly error messages** instead of technical errors
6. **Use optional chaining** (`?.`) for safer property access
7. **Validate API responses** before using data
8. **Show loading states** while fetching data
9. **Handle all HTTP status codes** (400, 404, 500)
10. **Log errors for debugging** but show clean messages to users
