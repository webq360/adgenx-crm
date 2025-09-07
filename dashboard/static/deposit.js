document.addEventListener('DOMContentLoaded', () => {
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step3 = document.getElementById('step-3');

    const stepCircle1 = document.getElementById('step-circle-1');
    const stepCircle2 = document.getElementById('step-circle-2');
    const stepCircle3 = document.getElementById('step-circle-3');

    const stepLabel1 = document.getElementById('step-label-1');
    const stepLabel2 = document.getElementById('step-label-2');
    const stepLabel3 = document.getElementById('step-label-3');

    const nextButton1 = document.getElementById('next-button-1');
    const nextButton2 = document.getElementById('next-button-2');
    const backButton2 = document.getElementById('back-button-2');

    const finalDetailsContainer = document.getElementById('final-details-container');
    const depositForm = document.getElementById('deposit-form');
    const receiptFile = document.getElementById('receiptFile');
    const uploadText = document.getElementById('upload-text');
    const bdtAmount = document.getElementById('bdtAmount');
    const txId = document.getElementById('txId');
    const amountDisplay = document.querySelector('.amount-display');

    let currentStep = 1;
    const paymentDetails = {};

    const updateStepUI = () => {
        step1.style.display = currentStep === 1 ? 'block' : 'none';
        step2.style.display = currentStep === 2 ? 'block' : 'none';
        step3.style.display = currentStep === 3 ? 'block' : 'none';

        stepCircle1.classList.toggle('active', currentStep >= 1);
        stepCircle2.classList.toggle('active', currentStep >= 2);
        stepCircle3.classList.toggle('active', currentStep >= 3);

        stepLabel1.classList.toggle('active', currentStep >= 1);
        stepLabel2.classList.toggle('active', currentStep >= 2);
        stepLabel3.classList.toggle('active', currentStep >= 3);
    };

    const validateStep2 = () => {
        const bdt = parseInt(bdtAmount.value);
        if (bdtAmount.value && txId.value && !isNaN(bdt) && bdt >= 100 && bdt <= 9000000 && receiptFile.files.length > 0) {
            nextButton2.disabled = false;
        } else {
            nextButton2.disabled = true;
        }
    };

    const bankOptions = document.querySelectorAll('.bank-option');
    bankOptions.forEach(option => {
        option.addEventListener('click', () => {
            bankOptions.forEach(opt => opt.classList.remove('selected'));
            option.classList.add('selected');
            paymentDetails.payment_method_id = option.dataset.methodId;

            document.querySelectorAll('.bank-details').forEach(details => {
                details.style.display = 'none';
            });
            const detailsId = `${option.id.replace('-button', '-details')}`;
            document.getElementById(detailsId).style.display = 'block';
        });
    });

    nextButton1.addEventListener('click', () => {
        currentStep = 2;
        updateStepUI();
    });

    bdtAmount.addEventListener('input', () => {
        let amount = bdtAmount.value;
        amount = amount.replace(/[^0-9]/g, '');
        bdtAmount.value = amount;

        const bdt = parseInt(amount);
        const dollarRate = parseFloat(bdtAmount.dataset.dollarRate);

        if (!isNaN(bdt) && bdt >= 100 && bdt <= 9000000 && dollarRate > 0) {
            const usdAmount = (bdt / dollarRate).toFixed(2);
            amountDisplay.textContent = `$${usdAmount}`;
            document.getElementById('hidden-usd-amount').value = usdAmount;
            bdtAmount.classList.remove('is-invalid');
        } else {
            amountDisplay.textContent = '$0.00';
            document.getElementById('hidden-usd-amount').value = '';
            if (amount) {
                bdtAmount.classList.add('is-invalid');
            } else {
                bdtAmount.classList.remove('is-invalid');
            }
        }
        validateStep2();
    });

    txId.addEventListener('input', validateStep2);

    receiptFile.addEventListener('change', () => {
        if (receiptFile.files.length > 0) {
            uploadText.textContent = receiptFile.files[0].name;
        }
        validateStep2();
    });

    nextButton2.addEventListener('click', () => {
        paymentDetails.bdt_amount = bdtAmount.value;
        paymentDetails.tx_id = txId.value;
        paymentDetails.receipt = receiptFile.files[0];
        const dollarRate = parseFloat(bdtAmount.dataset.dollarRate);
        paymentDetails.usd_amount = (parseFloat(bdtAmount.value) / dollarRate).toFixed(2);
        currentStep = 3;
        updateStepUI();

        const selectedOption = document.querySelector('.bank-option.selected');
        const methodName = selectedOption.innerText.trim();
        const methodDetailsElement = document.getElementById(`${selectedOption.id.replace('-button', '-details')}`);
        const methodDetails = methodDetailsElement.innerHTML;

        const finalDetailsHtml = `
            <div class="container py-4">
              <div class="row border border-0 border-md border-secondary-subtle rounded">
                <div class="col-md-6 px-3 px-md-4 py-3 py-md-4">
                  <p class="small fw-semibold mb-2">${methodName}</p>
                  <div class="d-flex align-items-start mb-3">
                    <img loading="lazy" alt="" src="${selectedOption.querySelector('img').src}" width="40" height="40" class="me-3" />
                    <div class="small lh-sm">
                      ${methodDetails}
                    </div>
                  </div>

                  <p class="small fw-semibold mb-1">Amount in BDT</p>
                  <p class="small mb-3">৳ ${paymentDetails.bdt_amount}</p>

                  <p class="small fw-semibold mb-1">Trx ID or Reference</p>
                  <p class="small mb-3">${paymentDetails.tx_id}</p>

                  <div class="d-flex align-items-center mb-1">
                    <i class="far fa-copy fa-lg text-secondary me-2"></i>
                    <p class="small fw-semibold mb-0">Receipt copy or screenshot</p>
                  </div>
                  <p class="small ms-4 mb-0">${paymentDetails.receipt ? paymentDetails.receipt.name : 'N/A'}</p>
                </div>

                <div class="col-md-6 px-3 px-md-4 py-3 py-md-4 vertical-line">
                  <p class="small fw-semibold mb-2">USD Amount:</p>
                  <p class="h5 fw-bold mb-3">${paymentDetails.usd_amount}</p>
                  <p class="small">Based on your current USD rate</p>
                </div>
              </div>

              <div class="d-flex justify-content-between mt-4">
                <button id="back-button-3" type="button" class="btn btn-secondary d-flex align-items-center">
                  <i class="fas fa-arrow-left me-2"></i> Back
                </button>
                <button id="finish-button" type="button" class="btn btn-success d-flex align-items-center">
                  Finish <i class="fas fa-arrow-right ms-2"></i>
                </button>
              </div>
            </div>
        `;
        finalDetailsContainer.innerHTML = finalDetailsHtml;
        const backButton3 = document.getElementById('back-button-3');
        const finishButton = document.getElementById('finish-button');
        backButton3.addEventListener('click', () => {
            currentStep = 2;
            updateStepUI();
        });
        finishButton.addEventListener('click', () => {
            finishButton.disabled = true;
            finishButton.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                Processing...
            `;
            document.getElementById('hidden-payment-method').value = paymentDetails.payment_method_id;
            document.getElementById('hidden-bdt-amount').value = paymentDetails.bdt_amount;
            document.getElementById('hidden-tx-id').value = paymentDetails.tx_id;
            document.getElementById('hidden-receipt').files = receiptFile.files;
            document.getElementById('hidden-usd-amount').value = paymentDetails.usd_amount;
            depositForm.submit();
        });
    });

    backButton2.addEventListener('click', () => {
        currentStep = 1;
        updateStepUI();
    });

    // Set initial payment method
    const firstBank = document.querySelector('.bank-option');
    if (firstBank) {
        firstBank.click();
    }
});
