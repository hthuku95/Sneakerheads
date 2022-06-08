var MainImg = document.getElementById("mainImg")
var small_images = document.getElementsByClassName("small-img")

small_images[0].onclick = function (){
    MainImg.src = small_images[0].src
}
small_images[1].onclick = function (){
    MainImg.src = small_images[1].src
}
small_images[2].onclick = function (){
    MainImg.src = small_images[2].src
}
small_images[3].onclick = function (){
    MainImg.src = small_images[3].src
}