Telegram.WebApp.expand()
Telegram.WebApp.ready()
u = document.getElementById('id_username')
p = document.getElementById('id_password')
t = document.getElementById('login')
tg = document.getElementById('tg')
tg.innerHTML = JSON.stringify(data)
u.value = data.id
p.value = data.id
t.children[3].click()

function updateBetslip(element) {
    var checked = document.querySelectorAll("input[type=checkbox]:checked");
    var betslipicon = document.getElementsByClassName('betslip-icon')[0]
    var odds = 1.0
    var betslip = document.getElementById('betslip')
    $("#betslip").empty()
    betslipicon.innerHTML = `<i class="fa-solid fa-file"></i>`;
    checked.forEach(check => {
        var odd = parseFloat(check.nextElementSibling.innerHTML)
        var home = check.parentElement.parentElement.parentElement.previousElementSibling.children[0].textContent
        var away = check.parentElement.parentElement.parentElement.previousElementSibling.children[1].textContent
        var pick = check.value
        var time = check.parentElement.parentElement.parentElement.parentElement.previousElementSibling.textContent
        var name = check.name
        odds = odds * odd
        var emptyEl = document.getElementById('betslip-container').cloneNode(true)
        emptyEl.setAttribute('id', name)
        emptyEl.classList.remove("hidden")
        emptyEl.children[1].innerHTML = odd
        emptyEl.children[0].children[1].children[0].innerHTML = home + ' Vs ' + away
        emptyEl.children[0].children[1].children[1].innerHTML = pick
        emptyEl.children[0].children[1].children[2].innerHTML = time
        betslip.append(emptyEl)
        var hzRule = document.createElement('hr');// make a hr
        betslip.append(hzRule)
    });
    var totalOdds = document.getElementsByClassName('total-odds')[0]
    totalOdds.innerHTML = odds.toFixed(2)
    var payout = document.getElementsByClassName('payout')[0]
    var amount = document.getElementsByClassName('amount')[0].value
    var winnings = (odds.toFixed(2) * amount)

    payout.innerHTML = currency + ' ' + winnings.toLocaleString()

    if (checked.length > 0) {
        betslipicon.innerHTML = `<div class='odds'><i>${checked.length}:</i><i> \n ${odds.toFixed(2)}</i></div>`;
        $('#submitBtn').removeAttr('disabled')

    }
    else {
        betslipicon.innerHTML = `<i class="fa-solid fa-file"></i>`;
        $('#submitBtn').attr('disabled')
    }
    var button = document.getElementById('submitBtn')
    var amountEl = document.getElementById('amount')
    if (parseInt(amountEl.value) > parseInt(balance)) {
        amountEl.style.color = 'red'
        button.setAttribute('disabled', '')
    }
    else {
        amountEl.style.color = 'black'
        button.removeAttribute('disabled')

    }
}
function updateChecked(element) {
    var $box = $(element);
    if ($box.is(":checked")) {
        // the name of the box is retrieved using the .attr() method
        // as it is assumed and expected to be immutable
        var group = "input:checkbox[name='" + $box.attr("name") + "']";
        // the checked state of the group/box on the other hand will change
        // and the current value is retrieved using .prop() method
        $(group).prop("checked", false);
        $(group).parent().parent().css("background-color", "#e8e8e8")

        $box.prop("checked", true);
        $box.parent().parent().css("background-color", "#04A777")
    } else {
        $box.prop("checked", false);
        $box.parent().parent().css("background-color", "#e8e8e8")

    }
    updateBetslip()
}
function removeMatch(element) {
    matchId = element.parentElement.parentElement.id
    match = document.getElementsByName(matchId)
    pick = element.nextElementSibling.children[1].innerText

    match.forEach(choice => {
        choice.checked = false
        if (choice.value == pick) {
            choice.parentElement.parentElement.style.backgroundColor = '#e8e8e8'
        }
    });
    updateBetslip()
}
function makeActive(id) {
    $element = $(id)
    $navs = $('.nav')
    $navs.each(function () {
        if ($(this).attr('id') != $element.attr('id')) {
            $(this).addClass('hidden')
        }
        else {
            $(this).removeClass('hidden')
        }
    });
}


function toggleDisable(element) {
    button = element.parentElement.nextElementSibling
    if (element.value != '') {
        button.removeAttribute('disabled')
    }
    else {
        button.setAttribute('disabled', '')
    }
}


function showMore(element) {
    bets = element.parentElement.parentElement.nextElementSibling
    bets.classList.toggle('hidden')
    element.parentElement.classList.toggle('hidden')
    down = document.getElementsByClassName('down')[0]
}

function showLess(element) {
    bets = element.parentElement.parentElement
    bets.classList.toggle('hidden')
    // element.parentElement.classList.toggle('hidden')
    down = document.getElementsByClassName('down')[0]
    down.classList.toggle('hidden')
}

function copyContent() {
    let copyText = document.getElementById('dep-address');
    // var copyText = document.getElementById("myInput");
    copyText.focus();
    navigator.clipboard
        .writeText(copyText.innerText)
        .then(() => {
            $.toast({
                heading: 'Success!',
                text: 'Copied to clipboad',
                showHideTransition: 'slide',
                position: 'top-right',
                hideAfter: 5000,
                icon: 'success'
            })
        })
        .catch(() => {
            $.toast({
                heading: 'Failed!',
                text: 'Something went wrong',
                showHideTransition: 'slide',
                position: 'top-right',
                hideAfter: 4000,
                icon: 'error'
            })
        });
    showTrx()
}

async function pasteContent(element) {
    let sib = element.previousElementSibling
    let input = sib.previousElementSibling

    try {
        sib.classList.add('hidden')
        navigator.clipboard.readText().then(
            clipText => input.value = clipText);
        // const text = await navigator.clipboard.readText()
        // input.value = text;
        console.log('Text pasted.');
    } catch (error) {
        console.log('Failed to read clipboard');
    }
}
function showTrx() {
    trx = document.getElementById('trx')
    trx.classList.remove('hidden')
}
function updateBalances(deposit) {
    let betslip_balance = document.getElementsByClassName('account-balance')[0]
    let main_balance_WLD = document.getElementsByClassName('main-balance')[0].children[1].children[1]
    let main_balance_local = document.getElementsByClassName('main-balance')[0].children[1].children[2]
    let local = main_balance_local.innerText.split(' ')[0]
    let exchrate = parseFloat(main_balance_local.innerText.split(' ')[1]) / parseFloat(main_balance_WLD.innerText.split(' ')[1])
    main_balance_WLD.innerText = `WLD ${(parseFloat(main_balance_WLD.innerText.split(' ')[1]) + deposit).toFixed(2)}`
    betslip_balance.innerText = `${local} ${(parseFloat(betslip_balance.innerText.split(' ')[1]) + deposit * exchrate).toFixed(2)}`
    main_balance_local.innerText = betslip_balance.innerText
}

function showAddr(button) {
    let cont = document.createElement('div')
    let bar = document.createElement('div')
    bar.setAttribute('id', 'myBar')
    cont.appendChild(bar)
    button.parentNode.replaceChild(cont, button)

    async function show() {
        await new Promise(resolve => setTimeout(resolve, 1000));
        addr = document.getElementById('addr');
        addr.classList.remove('hidden');
        cont.classList.add('hidden');
    }

    show();

}
function hideDeposit() {
    form = document.getElementById('deposit-form')
    form.innerHTML = '<div id="myProgress"><div id="myBar"></div><div class="text">connecting to blockchain</div></div>'
}

async function checkTrx() {
    let form = document.getElementById('deposit-form')
    values = form.getElementsByTagName('input')
    let data = new FormData();

    for (let index = 0; index < values.length; index++) {
        data.append(values[index].name, values[index].value)
    }
    hideDeposit()
    try {
        const response = await fetchWithTimeout("/trx/", {
            method: "POST",
            body: data,
            headers: { "X-CSRFToken": '{{csrf_token}}' },
            timeout: 35000,
        });
        const resp = await response.json();
        if (await resp['result'] == 1) {
            $.toast({
                heading: 'success!',
                text: 'Deposit successfully',
                showHideTransition: 'slide',
                position: 'top-right',
                hideAfter: 5000,
                icon: 'success'
            })
            console.log(resp['value'])
            updateBalances(resp['value'])
        }
        else {
            $.toast({
                heading: 'Error!',
                text: 'This transaction has been recorded',
                showHideTransition: 'slide',
                position: 'top-right',
                hideAfter: 5000,
                icon: 'warning'
            })
        }

    }
    catch (error) {
        console.log(error)
        $.toast({
            heading: 'Info!',
            text: 'transaction has not reflected,please wait before trying again',
            showHideTransition: 'slide',
            position: 'top-right',
            hideAfter: 5000,
            icon: 'info'
        })
    }
    form.innerHTML = '<form id="deposit-form" action="/transact/" method="post"><input type="hidden" name="csrfmiddlewaretoken" value="vKSI5zOQiJUMgVMmicjL5VGlNHezfgYjq2QJMXmqDLNSXHCyrCM5xqbqB9w8fBMm"><div class="request"><div class="wrapper addr hidden" id="addr"><span class="address">0XAedzrESssGDZS#442Q</span><div class="copy" onclick="copyContent()"><i class="fa-solid fa-copy"></i> COPY</div></div><div class="hidden" id="trx"><div class="wrapper"><input type="text" name="trxcode" id="trxcode"><span class="hash">enter transaction hash</span><div class="copy" onclick="pasteContent()"><i class="fa-solid fa-clipboard"></i> PASTE</div></div><div><p class="small tut"><i class="fa-regular fa-circle-question"></i>How to find hash</p><button type="button" onclick="checkTrx()">Confirm Deposit</button></div></div><button type="button" onclick="showAddr(this)">request deposit address</button></div>'
}
async function fetchWithTimeout(resource, options = {}) {
    const { timeout = 35000 } = options;
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    const response = await fetch(resource, { ...options, signal: controller.signal });
    clearTimeout(id);
    return response
}




function hideSpan(element){
    let sib = element.nextElementSibling
    sib.classList.add('hidden')
}
function showSpan(element){
    let sib = element.nextElementSibling
    sib.classList.remove('hidden')
}





