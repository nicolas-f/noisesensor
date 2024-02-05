
function StrToArrayBuffer(byteStr) {
  var bytes = new Uint8Array(byteStr.length)
  for (var i = 0; i < byteStr.length; i++) {
    bytes[i] = byteStr.charCodeAt(i)
  }
  return bytes.buffer
}

function base64StringToArrayBuffer(b64str) {
  return StrToArrayBuffer(atob(b64str));
}

function convertPemToBinary(pem) {
  var lines = pem.split('\n')
  var encoded = ''
  for(var i = 0;i < lines.length;i++){
    if (lines[i].trim().length > 0 &&
        lines[i].indexOf('-BEGIN') < 0 &&
        lines[i].indexOf('-END') < 0) {
      encoded += lines[i].trim()
    }
  }
  return base64StringToArrayBuffer(encoded);
}

/*
Import a PEM encoded RSA private key, to use for RSA-PSS signing.
Takes a string containing the PEM encoded key, and returns a Promise
that will resolve to a CryptoKey representing the private key.
*/
function importPrivateKey(pem) {
      // convert from a binary string to an ArrayBuffer
      const binaryDer = convertPemToBinary(pem);

      return window.crypto.subtle.importKey(
        "pkcs8",
        binaryDer,
        {
          name: "RSA-OAEP",
          hash: {name: "SHA-256"},
        },
        true,
        ["decrypt"]
      );
}
function stringToArrayBuffer(str){
    var buf = new ArrayBuffer(str.length);
    var bufView = new Uint8Array(buf);
    for (var i=0, strLen=str.length; i<strLen; i++) {
        bufView[i] = str.charCodeAt(i);
    }
    return buf;
}

function arrayBufferToString(str){
    var byteArray = new Uint8Array(str);
    var byteString = '';
    for(var i=0; i < byteArray.byteLength; i++) {
        byteString += String.fromCodePoint(byteArray[i]);
    }
    return byteString;
}

function encryptDataWithPublicKey(data, key) {
    data = stringToArrayBuffer(data);
    return window.crypto.subtle.encrypt(
    {
        name: "RSA-OAEP",
        //label: Uint8Array([...]) //optional
    },
    key, //from generateKey or importKey above
    data //ArrayBuffer of data you want to encrypt
);
}


function decryptDataWithPrivateKey(data, key) {
    data = stringToArrayBuffer(data);
    return window.crypto.subtle.decrypt(
        {
            name: "RSA-OAEP",
            //label: Uint8Array([...]) //optional
        },
        key, //from generateKey or importKey above
        data //ArrayBuffer of data you want to encrypt
    );
}


async function do_decrypt(jsonContent) {
    const pem = await $('input[name="privkey"]')[0].files[0].text();
    var encrypted = atob(jsonContent.hits.hits[0]._source.samples);
    var tstamp = jsonContent.hits.hits[0]._source.timestamp;
    var date = new Date(tstamp);
    // convert a Forge certificate from PEM
    const pki = forge.pki;
    var privateKey = pki.decryptRsaPrivateKey(pem, $('input[name="pwd"]')[0].value);
    let el = document.getElementById("error_panel");
    if(privateKey == null) {
        el.style.visibility = "visible";
        el.innerHTML = "Invalid decryption key or password";
    } else {
        el.style.visibility = "hidden";
        var decrypted = privateKey.decrypt(encrypted.substring(0, 512), 'RSA-OAEP');
        var aes_key = decrypted.substring(0, 16);
        var iv = decrypted.substring(16, 32);
        console.log("aeskey " + btoa(aes_key));
        console.log("iv " + btoa(iv));
        //('aes_key :', 'wJyLYu1QrppXkVr4VkiN2g==')
        //('iv :', 'PclNb35dRhvq90Bvc9JjvA==')
        var decipher = forge.cipher.createDecipher('AES-CBC', aes_key);
        decipher.start({iv: iv});
        decipher.update(forge.util.createBuffer(encrypted.substring(512)));
        var result = decipher.finish(); // check 'result' for true/false
        // outputs decrypted hex
        const fname = date.toLocaleDateString()+"_"+date.toLocaleTimeString()+".ogg";
        download(decipher.output.data, fname, "audio/ogg");
    }
}

function decrypt_and_download(sample_id) {
    $.ajax({
      type: "GET",
      url: "get-samples/"+btoa(sample_id),
      success: function(jsonContent) {
            do_decrypt(jsonContent);
      },
      contentType : 'application/json',
    });
}

function download_all() {
    downloadedData.forEach(function(el) {
        decrypt_and_download(el["elementid"]);
    });
}

function fetch() {
    var dateStart = $('input[name="datetimes"]').data('daterangepicker').startDate.valueOf();
    var dateEnd = $('input[name="datetimes"]').data('daterangepicker').endDate.valueOf();

    $.ajax({
      type: "GET",
      url: "/api/list-samples/"+dateStart+"/"+dateEnd,
      success: function(jsonContent) {
        downloadedData.length = 0;
        jsonContent.forEach(function(element) {
            entry = {};
            entry["id"]="<a href=\"#\" onclick=\"decrypt_and_download('"+element["_id"]+"')\">Download</a>";
            entry["elementid"] = element["_id"];
            var date = new Date(parseInt(element["timestamp"][0]));
            entry["timestamp"]=date.toLocaleDateString()+" "+date.toLocaleTimeString();
            entry["hwa"]=element["hwa"];
            downloadedData.push(entry);
        });
        stations.render();
        document.getElementById('download_all_button').disabled = false;
      },
      contentType : 'application/json',
    });
}
function add_template() {
    var col = results.countRows();
    results.alter('insert_row', col, 2);
    resultsTable[resultsTable.length - 1] = new Array(fields.length).fill(1.0);
    results.render();
}

function remove_template() {
    var col = results.countRows();
    if(col > 2) {
        results.alter('remove_row', results.countRows() - 1);
        results.alter('remove_row', results.countRows() - 1);
    }
}

function configure() {
    var dateStart = $('input[name="datetimes"]').data('daterangepicker').startDate.valueOf();
    var dateEnd = $('input[name="datetimes"]').data('daterangepicker').endDate.valueOf();

    var startHour = $('input[name="startHour"]')[0].value;
    var endHour = $('input[name="endHour"]')[0].value;
    // Extract spectrums and weigth arrays
    spectrum_arrays = [];
    weight_arrays = [];
    for(var i=0; i < resultsTable.length; i+=2) {
        spectrum_arrays.push(resultsTable[i]);
    }
    for(var i=1; i < resultsTable.length; i+=2) {
        weight_arrays.push(resultsTable[i]);
    }

    // generate json to post
    var jsonQuery = {
        date_start : dateStart,
        date_end : dateEnd,
        spectrum : spectrum_arrays,
        weight : weight_arrays,
        cosine : parseFloat($('input[name="cos_threshold"]')[0].value),
        min_leq : parseFloat($('input[name="minleq"]')[0].value),
        cached_length : parseInt($('input[name="minlength"]')[0].value),
        total_length : parseInt($('input[name="maxlength"]')[0].value),
        trigger_count : parseInt($('input[name="triggerday"]')[0].value)
         };

    if(startHour != "") {
        jsonQuery["start_hour"] = startHour;
    }

    if(endHour != "") {
        jsonQuery["end_hour"] = endHour;
    }
    var el = document.getElementById("error_panel");
    var el2 = document.getElementById("info_panel");
    if($('input[name="pubkey"]')[0].files.length==0) {
        el.style.visibility = "visible";
        el.innerHTML = "Please select the public encryption key";
        $('html, body').animate({ scrollTop: 0 }, 'fast');
    } else{
        el.style.visibility = "hidden";
        el2.style.visibility = "hidden";
    }
    $('input[name="pubkey"]')[0].files[0].text().then(function(value) {
        jsonQuery["file"] = value;

        $.ajax({
          type: "POST",
          url: "set-trigger",
          data: JSON.stringify(jsonQuery),
          success: function(val) {
            if(val["result"] != 'success') {
                el.style.visibility = "visible";
                el.innerHTML = "Invalid public encryption key. Reason :" + val["result"];
                el2.style.visibility = "hidden";
            } else{
                el.style.visibility = "hidden";
                el2.style.visibility = "visible";
                el2.innerHTML = "Trigger set";
            }
          },
          contentType : 'application/json',
        });


        $('html, body').animate({ scrollTop: 0 }, 'fast');
    });

}