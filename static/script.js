$('#topup-form').submit(function(e){
  e.preventDefault()
  var dict = {
    payment_id : $('#agen-bank').val(), 
    gross_amount:$('#gross_amount').val(),
    topup_id: 'topup-' + Math.floor(Date.now() * Math.random())
  };

  $.ajax({
      type: "POST", 
      url: "/payment/topup", //localhost Flask
      data : JSON.stringify(dict),
      contentType: "application/json",
      success: function (resp) {
        // alert("Access Token :\n"+data.access_token)
        console.log(resp)
        alert(resp.message+"\nPayment Code/VA Number: "+(resp.data.payment_code||resp.data.va_numbers[0].va_number)+"\nJumlah Tagihan: "+resp.data.gross_amount)
      },
      error: function (resp) {
        // alert(data.responseJSON.msg)
        console.log(resp)
      },
  });
})