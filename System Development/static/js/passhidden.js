function togglePW()
{
    var password = document.querySelector('[name=password]');
    var cpassword = document.querySelector('[name=cpassword]');

    if (password.getAttribute('type')==='password')
    {
        password.setAttribute('type', 'text');
        document.getElementById("font").style.color='grey'
    }
    else
    {
        password.setAttribute('type','password');
        document.getElementById("font").style.color='black'
    }
}
function toggleCPW()
{
    var cpassword = document.querySelector('[name=cpassword]');

    if (cpassword.getAttribute('type')==='password')
    {
        cpassword.setAttribute('type', 'text');
        document.getElementById("font1").style.color='grey'
    }
    else
    {
        cpassword.setAttribute('type','password');
        document.getElementById("font1").style.color='black'
    } 
}