import axios from 'axios';

const client = axios.create({
    // 'baseURL': 'http://localhost:8000'
    withCredentials: false,
    headers: {
        'Content-Type': 'application/json'
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