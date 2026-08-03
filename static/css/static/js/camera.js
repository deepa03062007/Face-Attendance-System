const video = document.getElementById("video");

navigator.mediaDevices.getUserMedia({
    video: true
})
.then(function(stream){
    video.srcObject = stream;
});

function captureImage(){

    const canvas = document.createElement("canvas");

    canvas.width = video.videoWidth;

    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");

    ctx.drawImage(video,0,0);

    const image = canvas.toDataURL("image/jpeg");

    fetch("/recognize",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({
            image:image
        })

    })

    .then(res=>res.json())
    .then(data=>{

        if(data.status=="saved"){

            document.getElementById("status").innerHTML=
            "Captured : "+data.count+"/30";

        }

        else if(data.status=="success"){

            document.getElementById("result").innerHTML=
            "✅ Attendance Marked : "+data.name;

        }

        else{

            document.getElementById("result").innerHTML=
            "❌ Unknown Face";

        }

    });
}
