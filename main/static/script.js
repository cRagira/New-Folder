function updateBetslip() {
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
    var winnings=(odds.toFixed(2) * amount)

    payout.innerHTML = currency +' '+ winnings.toLocaleString()

    if (checked.length > 0) {
        betslipicon.innerHTML = `<div class='odds'><i>${checked.length}:</i><i> \n ${odds.toFixed(2)}</i></div>`;
        $('#submitBtn').removeAttr('disabled')

    }
    else {
        betslipicon.innerHTML = `<i class="fa-solid fa-file"></i>`;
        $('#submitBtn').attr('disabled')
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
    })


        ;
}


var x, i, j, l, ll, selElmnt, a, b, c;
/* Look for any elements with the class "custom-select": */
x = document.getElementsByClassName("custom-select");
l = x.length;
for (i = 0; i < l; i++) {
    selElmnt = x[i].getElementsByTagName("select")[0];
    ll = selElmnt.length;
    /* For each element, create a new DIV that will act as the selected item: */
    a = document.createElement("DIV");
    a.setAttribute("class", "select-selected");
    a.innerHTML = selElmnt.options[selElmnt.selectedIndex].innerHTML;
    x[i].appendChild(a);
    /* For each element, create a new DIV that will contain the option list: */
    b = document.createElement("DIV");
    b.setAttribute("class", "select-items select-hide");
    for (j = 1; j < ll; j++) {
        /* For each option in the original select element,
        create a new DIV that will act as an option item: */
        c = document.createElement("DIV");
        c.innerHTML = selElmnt.options[j].innerHTML;
        c.addEventListener("click", function (e) {
            /* When an item is clicked, update the original select box,
            and the selected item: */
            var y, i, k, s, h, sl, yl;
            s = this.parentNode.parentNode.getElementsByTagName("select")[0];
            sl = s.length;
            h = this.parentNode.previousSibling;
            for (i = 0; i < sl; i++) {
                if (s.options[i].innerHTML == this.innerHTML) {
                    s.selectedIndex = i;
                    h.innerHTML = this.innerHTML;
                    y = this.parentNode.getElementsByClassName("same-as-selected");
                    yl = y.length;
                    for (k = 0; k < yl; k++) {
                        y[k].removeAttribute("class");
                    }
                    this.setAttribute("class", "same-as-selected");
                    break;
                }
            }
            h.click();
        });
        b.appendChild(c);
    }
    x[i].appendChild(b);
    a.addEventListener("click", function (e) {
        /* When the select box is clicked, close any other select boxes,
        and open/close the current select box: */
        e.stopPropagation();
        closeAllSelect(this);
        this.nextSibling.classList.toggle("select-hide");
        this.classList.toggle("select-arrow-active");
    });
}

function closeAllSelect(elmnt) {
    /* A function that will close all select boxes in the document,
    except the current select box: */
    var x, y, i, xl, yl, arrNo = [];
    x = document.getElementsByClassName("select-items");
    y = document.getElementsByClassName("select-selected");
    xl = x.length;
    yl = y.length;
    for (i = 0; i < yl; i++) {
        if (elmnt == y[i]) {
            arrNo.push(i)
        } else {
            y[i].classList.remove("select-arrow-active");
        }
    }
    for (i = 0; i < xl; i++) {
        if (arrNo.indexOf(i)) {
            x[i].classList.add("select-hide");
        }
    }
}

/* If the user clicks anywhere outside the select box,
then close all select boxes: */
document.addEventListener("click", closeAllSelect);
function toggleDisable(element) {
    button=element.parentElement.nextElementSibling
    if (element.value != '') {
        button.removeAttribute('disabled')
    }
    else{
        button.setAttribute('disabled','')
    }
}
function showMore(element){
    bets=element.parentElement.parentElement.nextElementSibling
    bets.classList.toggle('hidden')
    element.parentElement.classList.toggle('hidden')
    down=document.getElementsByClassName('down')[0]
}

function showLess(element){
    bets=element.parentElement.parentElement
    bets.classList.toggle('hidden')
    // element.parentElement.classList.toggle('hidden')
    down=document.getElementsByClassName('down')[0]
    down.classList.toggle('hidden')
}