<?php
session_start();
$conn = mysqli_connect("localhost","ikhsan","qqqq","ta");
 
//menambahkan data baru
if(isset($_POST['tambahkandata'])){
    $platkendaraan = $_POST['platkendaraan']; 
    $namapengendara = $_POST['namapengendara'];
    $alamat = $_POST['alamat'];
    $notelepon = $_POST['notelepon'];
    $email = $_POST['email'];

    $addtotable = mysqli_query($conn,"insert into pengendara (namapengendara, platkendaraan, alamat, notelepon, email) values('$namapengendara', '$platkendaraan','$alamat','$notelepon','$email')");
    if($addtotable){
        header('location:index.php');
    } else {
        echo 'Gagal';
        header('location:index.php'); 
    }
}
?> 
