$(document).ready(function() {
  // scroll instantly to bottom of messages on load
  $(window).scrollTop($(document).height());
  if ($(window).width() < 768) {
    $('#main-nav').remove();
  }

  var sessionKey = $('#sessionKey').text();
  socket = new WebSocket("ws://" + window.location.host + "/chat" + window.location.pathname);

  socket.onmessage = function(message) {
      console.log(message);
      var data = JSON.parse(message.data);
      var currentUser = $('#chatData #user').text();

      var html;
      if (data.user == currentUser) {
        html = "<div class='message-box message-sent' data-mssg-id='"+ data.message_id +"'><div class='text'>" + data.message + "</div></div>";
      } else {
        html = "<div class='message-box message-received' data-mssg-id='"+ data.message_id +"'><div class='sender'>" + data.user + "</div><div class='text'>" + data.message + "</div></div>";
      }
      $("#messages").append(html);

      // scroll instantly to bottom of page upon new message receival
      $(window).scrollTop($(document).height());
  }

  socket.onopen = function() {
      console.log("socked opened");
  }

  // Call onopen directly if socket is already open
  if (socket.readyState == WebSocket.OPEN) socket.onopen();

  $("#messageInput").on('keypress', function(e) {
    if (e.which == 13) {
      var message = {
          user: $('#user').text(),
          message: $('#messageInput').val()
      }

      socket.send(JSON.stringify(message));
      $(this).val('');

      return false;
    }
  });
});


// like message box if clicked twice
$('.message-box').on('dblclick', function() {
  // send get request to like message
  var messageId = $(this).data('mssg-id');
  $.get('/message/like/' + messageId, function(data) {
    console.log(data);
  });
});
