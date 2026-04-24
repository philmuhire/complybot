// CloudFront Function (viewer-request). S3 REST has no "directory index": map
// /foo and /foo/ to /foo/index.html for Next static export (out/foo/index.html).
function handler(event) {
  var request = event.request;
  var uri = request.uri;
  if (uri === "/" || uri === "") {
    return request;
  }
  if (uri.indexOf("/_next/") === 0) {
    return request;
  }
  var segs = uri.split("/");
  var last = segs[segs.length - 1];
  if (last.indexOf(".") > -1) {
    return request;
  }
  if (uri.charAt(uri.length - 1) === "/") {
    request.uri = uri + "index.html";
  } else {
    request.uri = uri + "/index.html";
  }
  return request;
}
