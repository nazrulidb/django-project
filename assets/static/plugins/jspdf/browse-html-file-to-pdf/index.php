<HTML>
<HEAD>
<TITLE>Convert HTML file to PDF</TITLE>
<link href="./assets/css/style.css" type="text/css" rel="stylesheet" />
<script src="./vendor/jquery/jquery-3.2.1.min.js"></script>
</HEAD>
<BODY>
    <div id="container">
        <h1>Convert HTML file to PDF</h1>
        <form name="foo" method="post" class="input-form"
            enctype="multipart/form-data">
            <div class="row">
                <label class="form-label">Upload HTML file: </label> <input
                    type="file" id="fileUpload" name="file"
                    class="input-file" accept=".html,.htm">
            </div>
            <div class="preview">
                <div id="temp-target"></div>
            </div>
            <div class="row">
                <input type="button" value="Show Preview"
                    class="btn-preview" onclick="readHTML()"><span
                    id="error-message" class="error"></span> <input
                    type="button" value="Generate PDF"
                    class="btn-generate" onclick="converHTMLFileToPDF()">
            </div>

        </form>
    </div>
    <script src="./node_modules/jspdf/dist/jspdf.umd.min.js"></script>
    <script type="text/javascript"
        src="./node_modules/html2canvas/dist/html2canvas.js"></script>
    <script src="assets/js/convert.js"></script>
</BODY>
</HTML>