document.addEventListener('DOMContentLoaded', function() {
    fetch('http://localhost:5000/api/matches') // Используйте URL вашего API
        .then(response => response.json())
        .then(data => {
            const matchesDiv = document.getElementById('matches');
            data.forEach(match => {
                const matchElement = document.createElement('div');
                matchElement.innerHTML = `
                    <h2>Матч ${match.team1} против ${match.team2}</h2>
                    <p>Время: ${match.match_time}</p>
                    <p>Коэффициенты: Победа - ${match.coefficient_win}, Ничья - ${match.coefficient_draw}, Поражение - ${match.coefficient_lose}</p>
                    <p>Статус: ${match.status}</p>
                `;
                matchesDiv.appendChild(matchElement);
            });
        })
        .catch(error => console.error('Ошибка:', error));
});
