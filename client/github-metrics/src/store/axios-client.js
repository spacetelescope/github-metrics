import axios from 'axios';

const client = axios.create({
    baseURL: 'https://github-metrics-stsci-edu-prod.s3.amazonaws.com',
    withCredentials: false,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
});

// client.interceptors.response.use(function (response) {
//     return response
// }, function (error) {

// })

export const EncodeParams = (params) => {
    let result = []
    var key
    for(key in params) {
        result.push([key, encodeURIComponent(params[key])].join('='))
    }
    return result.join('&')
}
export default client;