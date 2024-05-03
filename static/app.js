$('.word').on('click', hideWord);
$('#restart').on('click', resetGame);
$('.fa-heart').on('click', toggleFave);
$('.fa-heart').hover(fillHeart);

// Gameplay funtion: hides word when clicked on
function hideWord(e) {
    e.preventDefault();
    e.target.style.color = 'rgba(255, 0, 0, 0.0)';
}

// Gameplay function: reveals words again to restart
function resetGame(e) {
    e.preventDefault();
    $('.card-body').find('span, li, i').css('color', 'black');
}

// Adds/removes verse from users favorites list
function toggleFave(e) {
    e.target.classList.toggle('fa-solid'); // class of favorite
    e.target.classList.toggle('fa-regular'); // class of non-favorite
}

// Fills heart icon when mouse hovers
function fillHeart(e) {
    e.target.classList.toggle('fa-solid'); // class of favorite
}