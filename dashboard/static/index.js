const ad_accounts_data_element = document.getElementById('ad_accounts_data_json');
const ad_accounts_data = JSON.parse(ad_accounts_data_element.textContent);
const topupModal = document.getElementById('topupModal');
const topupMessage = document.getElementById('topup-message');

topupModal.addEventListener('show.bs.modal', function (event) {
    const button = event.relatedTarget;
    const adAccountId = button.getAttribute('data-ad-account-id');
    const adAccountIdInput = topupModal.querySelector('#ad-account-id');
    adAccountIdInput.value = adAccountId;
    topupMessage.innerHTML = ''; // Clear previous messages
    topupModal.querySelector('#amount').value = ''; // Clear previous amount
});

const topupForm = document.getElementById('topup-form');
topupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(topupForm);
    const response = await fetch('/topup/', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();

    if (result.success) {
        topupMessage.innerHTML = 'Top up successful!';
        topupMessage.style.color = 'green';
        setTimeout(() => {
            location.reload();
        }, 1000);
    } else {
        topupMessage.innerHTML = `Error: ${result.error}`;
        topupMessage.style.color = 'red';
    }
});

const adMbAccountModal = document.getElementById('adMbAccountModal');
const adMbAccountMessage = document.getElementById('ad-mb-account-message');

adMbAccountModal.addEventListener('show.bs.modal', function (event) {
    console.log('Add MB Account modal shown');
    const button = event.relatedTarget;
    const adAccountId = button.getAttribute('data-ad-account-id');
    const adAccountIdInput = adMbAccountModal.querySelector('#ad-mb-account-id');
    adAccountIdInput.value = adAccountId;
    adMbAccountMessage.innerHTML = ''; // Clear previous messages
    adMbAccountModal.querySelector('#mb-name').value = '';
    adMbAccountModal.querySelector('#mb-name').defaultValue = ''; // Clear previous mb name
    adMbAccountModal.querySelector('#mb-id').value = '';
    adMbAccountModal.querySelector('#mb-id').defaultValue = ''; // Clear previous mb id
    console.log('Cleared mb-name and mb-id');
});

const adMbAccountForm = document.getElementById('ad-mb-account-form');
adMbAccountForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(adMbAccountForm);
    const response = await fetch('/request_bm_account/', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();

    if (result.success) {
        adMbAccountMessage.innerHTML = 'Ad MB Account added successfully!';
        adMbAccountMessage.style.color = 'green';
        setTimeout(() => {
            location.reload();
        }, 1000);
    } else {
        adMbAccountMessage.innerHTML = `Error: ${result.error}`;
        adMbAccountMessage.style.color = 'red';
    }
});

const removeBmAccountModal = document.getElementById('removeBmAccountModal');
const removeBmAccountMessage = document.getElementById('remove-bm-account-message');
const bmAccountsCheckboxesDiv = document.getElementById('bm-accounts-checkboxes');

removeBmAccountModal.addEventListener('show.bs.modal', function (event) {
    console.log('Remove BM Account modal shown');
    const button = event.relatedTarget;
    const adAccountId = button.getAttribute('data-ad-account-id');
    const adAccountIdInput = removeBmAccountModal.querySelector('#remove-bm-account-ad-id');
    adAccountIdInput.value = adAccountId;
    removeBmAccountMessage.innerHTML = ''; // Clear previous messages
    bmAccountsCheckboxesDiv.innerHTML = ''; // Clear previous checkboxes
    console.log('Cleared previous messages and checkboxes');

    const adAccount = ad_accounts_data.find(acc => acc.id == adAccountId);
    console.log('Ad Account data:', adAccount);

    if (adAccount && adAccount.bm_accounts.length > 0) {
        console.log('Populating checkboxes for BM accounts:', adAccount.bm_accounts);
        adAccount.bm_accounts.forEach(bm => {
            const div = document.createElement('div');
            div.className = 'form-check';
            div.innerHTML = `
                <input class="form-check-input" type="radio" name="bm_account_id" value="${bm.id}" id="bm-${bm.id}">
                <label class="form-check-label" for="bm-${bm.id}">
                    ${bm.acc_name} (ID: ${bm.acc_id})
                </label>
            `;
            bmAccountsCheckboxesDiv.appendChild(div);
        });
    } else {
        console.log('No BM accounts found for this Ad Account.');
        bmAccountsCheckboxesDiv.innerHTML = '<p>No BM accounts connected to this Ad Account.</p>';
    }
});

const removeBmAccountForm = document.getElementById('remove-bm-account-form');
removeBmAccountForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(removeBmAccountForm);
    const response = await fetch('/remove_bm_account_request/', { // New URL for backend
        method: 'POST',
        body: formData
    });

    const result = await response.json();

    if (result.success) {
        removeBmAccountMessage.innerHTML = 'Remove BM Account request submitted successfully!';
        removeBmAccountMessage.style.color = 'green';
        setTimeout(() => {
            location.reload();
        }, 1000);
    } else {
        removeBmAccountMessage.innerHTML = `Error: ${result.error}`;
        removeBmAccountMessage.style.color = 'red';
    }
});