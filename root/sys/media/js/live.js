	// Comet connection to cloudpub 
	// This required for Orbited
        var TCPSocket = Orbited.TCPSocket;

        // Plugin that handle connetion
        jQuery.fn.bunch = function(path) {

            	var comet_port = 9999;
            	var client = new STOMPClient();
		var node = this;
		var id = p2id( path );

		var shutdown = false;		

		function status(message) {
			$('#status').html( message );
		}

		this.send = function( cmd ) {
			client.send( cmd, path );
			status( "SEND: " + cmd ); 
		}
	
		function connect() {
    			var cookie = $.cookie("sessionid");
    			client.connect(server, comet_port, cookie, path);
		}
	
		status("Connecting to: " + path );

	    	client.onopen = function() {
			status("You connected to: " + path );
    			window.onbeforeunload = function() {
				shutdown = true;
        			client.unsubscribe( path );
    			};
    		};

    		client.onclose = function(c) {
			status("Connection lost, Code:" + c);
			if(!shutdown) if( confirm("Connection to server lost. Try to reconnect?") ) connect();
    		};

    		client.onerror = function(error) {
        		status("ERROR: " + error); 
    		};

    		client.onerrorframe = function(frame) {
        		status("ERROR FRAME:  " + frame.body); 
    		};

    		client.onconnectedframe = function() {
        		client.subscribe( path );
			node.send( "!ls " + path );
    		};

    		client.onmessageframe = function(frame) { //check frame.headers.destination?
			var msg = $(frame.body);
			var id = msg.attr('id');
			if( !id ) {
				$('#status').html( msg );
				return;
			}
			var me = $('#'+id);
			if( me.length ) {
				me.replaceWith( msg ); 
			} else {
				var p = $( '#'+pid(id) );
				if( p.length ) msg.appendTo( p  ); 
			}
    		};

		connect();

		node.bind('click', function() {
			node.send("!ls " + path );
		}  );

		node.html('<root id="' + id + '"/>');
		return node;
	}; 

	function p2id( path ) {
		return path.replace("/","_");
	}

	function id2p( path ) {
		return path.replace("_","/");
	}

	function pid( path ) {
		var idx = path.lastIndexOf("_");
		if( idx > 0 ) return path.substring( 0, idx );
                return "_";
	}

        $( function() {
		var root = $("#pwd").bunch("/");
		$('#shell').bind('keypress', function(event) {
			if ((event.keyCode || event.which) == 13) { 
                              	var cmd = $(this).val();
				root.send( cmd );
				$(this).attr('value','');
				return false;
			}
		});
	});
 
